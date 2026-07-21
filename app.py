from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, send_from_directory, abort, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Kategori, Surat, AktivitasLog # Import database dari models.py
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime
import ai_engine
import os
from dotenv import load_dotenv

# Load konfigurasi dari file .env
load_dotenv()

# ── Import ReportLab untuk generate PDF ──────────────────────────────────────
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import HRFlowable

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_digisurat_2026' # Wajib ada untuk flash message/session

# ── Konfigurasi Database MySQL (dari file .env) ───────────────────────────────
_DB_HOST = os.getenv('DB_HOST', 'localhost')
_DB_PORT = os.getenv('DB_PORT', '3306')
_DB_USER = os.getenv('DB_USER', 'root')
_DB_PASSWORD = os.getenv('DB_PASSWORD', '')
_DB_NAME = os.getenv('DB_NAME', 'arsip_surat')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}'
    '?charset=utf8mb4'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True,
}
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Hubungkan app dengan database
db.init_app(app)

# ======================
# KONFIGURASI FLASK LOGIN
# ======================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index' # Jika belum login, dilempar ke rute 'index' (halaman login)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from flask import session

@app.before_request
def handle_multi_tab_sessions():
    if not session.get('multi_tab_active'):
        return

    admin_routes = ['dashboard_admin', 'manajemen_surat', 'kategori_surat', 'laporan_arsip', 'manajemen_user', 'pengaturan_ai', 'perbandingan_algoritma', 'pengaturan_akun_admin']
    karyawan_routes = ['dashboard_karyawan', 'pengaturan_akun']
    
    expected_role = None
    
    if request.endpoint in admin_routes:
        expected_role = 'Admin'
    elif request.endpoint in karyawan_routes:
        expected_role = 'Karyawan'
    elif request.referrer:
        if any(f"/{r}" in request.referrer for r in admin_routes):
            expected_role = 'Admin'
        elif any(f"/{r}" in request.referrer for r in karyawan_routes):
            expected_role = 'Karyawan'

    if expected_role:
        uid = session.get(f'uid_{expected_role}')
        if uid:
            if session.get('_user_id') != str(uid):
                user = User.query.get(uid)
                if user:
                    login_user(user)

# ======================
# HELPER LOG AKTIVITAS
# ======================
def log_aktivitas(user_id, kegiatan, status='Sukses'):
    try:
        new_log = AktivitasLog(user_id=user_id, kegiatan=kegiatan, status=status)
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gagal mencatat aktivitas: {e}")

# ======================
# ROUTE UTAMA & AUTH
# ======================
@app.route("/")
def index():
    # Jika sudah login, langsung lempar ke dashboard
    if current_user.is_authenticated:
        if current_user.role == 'Admin':
            return redirect(url_for("dashboard_admin"))
        else:
            return redirect(url_for("dashboard_karyawan"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("emailInput") 
    password = request.form.get("passwordInput")

    # Cari user di database berdasarkan email
    user = User.query.filter_by(email=email).first()

    # Cek apakah user ada DAN password cocok
    if user and check_password_hash(user.password, password):
        session['multi_tab_active'] = True
        session[f'uid_{user.role}'] = user.id
        login_user(user) # Daftarkan sesi user
        
        # Catat aktivitas login
        log_aktivitas(user.id, "Login ke sistem", "Sukses")

        if user.role == 'Admin':
            return redirect(url_for("dashboard_admin"))
        else:
            return redirect(url_for("dashboard_karyawan"))
    else:
        flash("Email atau password salah!", "error")
        return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        role = current_user.role
        user_id = current_user.id
        session.pop(f'uid_{role}', None)
        
        # Catat aktivitas logout
        log_aktivitas(user_id, "Logout dari sistem", "Sukses")
        
    logout_user() # Hapus sesi user
    
    if not session.get('uid_Admin') and not session.get('uid_Karyawan'):
        session.pop('multi_tab_active', None)
        
    return redirect(url_for("index"))

# ======================
# MENU ADMIN (Terproteksi Ketat)
# ======================
@app.route("/dashboard_admin")
@login_required
def dashboard_admin():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))
    return render_template("dashboard_admin.html")

@app.route("/manajemen_surat")
@login_required
def manajemen_surat():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))
    surat_list = Surat.query.order_by(Surat.created_at.desc()).all()
    kategori_list = Kategori.query.order_by(Kategori.nama.asc()).all()
    return render_template("manajemen_surat.html", surat_list=surat_list, kategori_list=kategori_list)

@app.route("/kategori_surat")
@login_required
def kategori_surat():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))
    return render_template("kategori_surat.html")

@app.route("/laporan_arsip")
@login_required
def laporan_arsip():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))

    kategori_filter = (request.args.get('kategori') or '').strip()
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()
    keyword = (request.args.get('keyword') or '').strip()

    query = Surat.query
    if kategori_filter:
        query = query.join(Kategori).filter(Kategori.nama == kategori_filter)
    if start_date:
        query = query.filter(Surat.tanggal_surat >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Surat.tanggal_surat <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if keyword:
        like_value = f'%{keyword}%'
        query = query.filter(
            or_(
                Surat.nomor_surat.ilike(like_value),
                Surat.pengirim.ilike(like_value),
                Surat.perihal.ilike(like_value),
            )
        )

    surat_list = query.order_by(Surat.tanggal_surat.desc(), Surat.created_at.desc()).all()
    kategori_list = Kategori.query.order_by(Kategori.nama.asc()).all()
    return render_template(
        'laporan_arsip.html',
        surat_list=surat_list,
        kategori_list=kategori_list,
        filters={
            'kategori': kategori_filter,
            'start_date': start_date,
            'end_date': end_date,
            'keyword': keyword,
        },
        total_count=len(surat_list),
    )

@app.route("/manajemen_user")
@login_required
def manajemen_user():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))
    return render_template("manajemen_user.html")

@app.route("/pengaturan_ai")
@login_required
def pengaturan_ai():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))
    return render_template("pengaturan_ai.html")

@app.route("/perbandingan_algoritma")
@login_required
def perbandingan_algoritma():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))
    return render_template("perbandingan_algoritma.html")

@app.route("/pengaturan_akun_admin")
@login_required
def pengaturan_akun_admin():
    if current_user.role != 'Admin':
        return redirect(url_for('pengaturan_akun'))
    return render_template("pengaturan_akun_admin.html")

# ======================
# MENU KARYAWAN (Terproteksi Ketat)
# ======================
@app.route("/dashboard_karyawan")
@login_required
def dashboard_karyawan():
    if current_user.role != 'Karyawan':
        return redirect(url_for('dashboard_admin'))
    return render_template("dashboard_karyawan.html")

@app.route("/pengaturan_akun")
@login_required
def pengaturan_akun():
    if current_user.role != 'Karyawan':
        return redirect(url_for('pengaturan_akun_admin'))
    return render_template("pengaturan_akun.html")

# ======================
# API MANAJEMEN USER (CRUD KE MYSQL)
# ======================

@app.route("/api/users", methods=["GET"])
@login_required
def get_users():
    users = User.query.all()
    output = []
    for u in users:
        output.append({
            "id": u.id,
            "nama": u.nama,
            "email": u.email,
            "role": u.role,
            "foto": u.foto
        })
    return jsonify(output)

@app.route("/api/users/add", methods=["POST"])
@login_required
def add_user():
    data = request.json
    try:
        role = data['role']
        # Pastikan hanya ada 1 akun untuk setiap role
        if User.query.filter_by(role=role).first():
            return jsonify({"status": "error", "message": f"Sudah ada akun dengan role {role}! Hanya diizinkan 1 akun."})
            
        new_user = User(
            nama=data['nama'],
            email=data['email'],
            password=generate_password_hash('digisurat123'), # Password default
            role=role,
        )
        db.session.add(new_user)
        db.session.commit()
        log_aktivitas(current_user.id, f"Menambahkan user baru: {data['nama']}", "Selesai")
        return jsonify({"status": "success", "message": "User berhasil ditambah"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/users/edit/<int:id>", methods=["PUT"])
@login_required
def edit_user_api(id):
    data = request.json
    user = User.query.get(id)
    if user:
        try:
            if data['role'] != user.role:
                if User.query.filter_by(role=data['role']).first():
                    return jsonify({"status": "error", "message": f"Sudah ada akun dengan role {data['role']}! Hanya diizinkan 1 akun."})
            user.nama = data['nama']
            user.email = data['email']
            user.role = data['role']
            db.session.commit()
            log_aktivitas(current_user.id, f"Mengubah data user: {data['nama']}", "Selesai")
            return jsonify({"status": "success", "message": "User berhasil diperbarui"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "User tidak ditemukan"})

@app.route("/api/users/reset_password/<int:id>", methods=["PUT"])
@login_required
def reset_password(id):
    user = User.query.get(id)
    if user:
        try:
            user.password = generate_password_hash('digisurat123')
            db.session.commit()
            log_aktivitas(current_user.id, f"Mereset password user: {user.nama}", "Selesai")
            return jsonify({"status": "success", "message": "Kata sandi berhasil di-reset ke default!"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "User tidak ditemukan"})

@app.route("/api/users/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_user_api(id):
    user = User.query.get(id)
    if user:
        nama_user = user.nama
        db.session.delete(user)
        db.session.commit()
        log_aktivitas(current_user.id, f"Menghapus user: {nama_user}", "Selesai")
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "User tidak ditemukan"})

# ======================
# API PROFIL
# ======================
@app.route("/api/profile/update", methods=["POST", "PUT"])
@login_required
def update_profile_api():
    try:
        if request.is_json:
            data = request.json
            current_user.nama = data.get('nama', current_user.nama)
            current_user.email = data.get('email', current_user.email)
        else:
            current_user.nama = request.form.get('nama', current_user.nama)
            current_user.email = request.form.get('email', current_user.email)
            
            foto = request.files.get('foto')
            if foto and foto.filename != '':
                filename = secure_filename(foto.filename)
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                new_filename = f"avatar_{current_user.id}.{ext}"
                foto_path = os.path.join(upload_folder, new_filename)
                
                foto.save(foto_path)
                current_user.foto = f"static/uploads/{new_filename}"

        db.session.commit()
        log_aktivitas(current_user.id, "Memperbarui profil", "Sukses")
        return jsonify({
            "status": "success", 
            "message": "Profil berhasil diperbarui",
            "foto_url": current_user.foto
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/profile/password", methods=["PUT"])
@login_required
def update_password_api():
    data = request.json
    old_pass = data['old_pass']
    new_pass = data['new_pass']
    if check_password_hash(current_user.password, old_pass):
        current_user.password = generate_password_hash(new_pass)
        db.session.commit()
        log_aktivitas(current_user.id, "Mengganti password", "Sukses")
        return jsonify({"status": "success", "message": "Password berhasil diperbarui"})
    else:
        return jsonify({"status": "error", "message": "Password lama tidak sesuai"})

@app.route("/api/profile/aktivitas", methods=["GET"])
@login_required
def get_aktivitas_api():
    aktivitas = AktivitasLog.query.filter_by(user_id=current_user.id).order_by(AktivitasLog.waktu.desc()).limit(50).all()
    output = []
    for a in aktivitas:
        # Konversi waktu ke format lokal atau string yg mudah dibaca
        output.append({
            "waktu": a.waktu.strftime("%d %b %Y, %H:%M"),
            "kegiatan": a.kegiatan,
            "status": a.status
        })
    return jsonify(output)

@app.route("/api/profile/aktivitas", methods=["DELETE"])
@login_required
def delete_aktivitas_api():
    try:
        AktivitasLog.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"status": "success", "message": "Riwayat aktivitas berhasil dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# ======================
# API MANAJEMEN SURAT (CRUD)
# ======================

def _normalize_surat_file_path(file_value):
    if not file_value:
        return 'static/uploads/surat_baru.pdf'
    file_value = str(file_value).replace('\\', '/').strip()
    if not file_value:
        return 'static/uploads/surat_baru.pdf'
    if file_value.startswith('static/uploads/'):
        return file_value
    if file_value.startswith('/'):
        return os.path.relpath(file_value, app.root_path).replace('\\', '/')
    return f'static/uploads/{os.path.basename(file_value)}'


def _ensure_upload_dir():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def _save_uploaded_surat_file(uploaded_file):
    if not uploaded_file or not getattr(uploaded_file, 'filename', None):
        return _normalize_surat_file_path(None)

    _ensure_upload_dir()
    filename = secure_filename(uploaded_file.filename)
    if not filename:
        return _normalize_surat_file_path(None)

    name, ext = os.path.splitext(filename)
    if not ext:
        ext = '.pdf'

    unique_filename = f"surat_{datetime.now().strftime('%Y%m%d%H%M%S')}_{name}{ext}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    uploaded_file.save(save_path)
    return os.path.relpath(save_path, app.root_path).replace('\\', '/')


def _delete_surat_file(file_path):
    try:
        normalized = _normalize_surat_file_path(file_path)
        if not normalized.startswith('static/uploads/'):
            return
        abs_path = os.path.join(app.root_path, *normalized.split('/'))
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except Exception:
        pass


def _get_or_create_kategori(kategori_nama):
    kategori_name = (kategori_nama or 'Umum').strip() or 'Umum'
    kat = Kategori.query.filter_by(nama=kategori_name).first()
    if not kat:
        kat = Kategori(nama=kategori_name)
        db.session.add(kat)
        db.session.commit()
    return kat


def _save_surat_from_fields(data, user_id=None):
    return _create_surat_from_payload(data, user_id=user_id, file_storage=None)


def _create_surat_from_payload(data, user_id=None, file_storage=None):
    nomor = (data.get('nomor') or '').strip()
    pengirim = (data.get('pengirim') or '').strip().rstrip(',').strip()
    perihal = (data.get('perihal') or '').strip()
    kategori_nama = (data.get('kategori') or 'Umum').strip() or 'Umum'

    if not nomor or not pengirim or not perihal:
        return {'saved': False, 'message': 'Nomor, pengirim, dan perihal wajib diisi.'}

    tanggal_str = (data.get('tanggal') or '').strip()
    if tanggal_str:
        try:
            tgl_obj = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
        except ValueError:
            tgl_obj = datetime.now().date()
    else:
        tgl_obj = datetime.now().date()

    if Surat.query.filter_by(nomor_surat=nomor).first():
        return {'saved': False, 'message': f'Nomor surat {nomor} sudah ada di arsip.'}

    kat = _get_or_create_kategori(kategori_nama)
    file_path = _save_uploaded_surat_file(file_storage) if file_storage else _normalize_surat_file_path(data.get('file') or data.get('file_path'))
    if not file_path:
        file_path = 'static/uploads/surat_baru.pdf'

    surat = Surat(
        nomor_surat=nomor,
        tanggal_surat=tgl_obj,
        pengirim=pengirim,
        perihal=perihal,
        file_path=file_path,
        kategori_id=kat.id,
    )
    db.session.add(surat)
    db.session.commit()

    if user_id:
        log_aktivitas(user_id, f'Menambahkan surat: {nomor}', 'Selesai')

    return {
        'saved': True,
        'message': 'Surat berhasil diarsipkan.',
        'surat_id': surat.id,
        'kategori': kategori_nama,
    }


def _update_surat_from_payload(surat, data, user_id=None, file_storage=None):
    nomor = (data.get('nomor') or '').strip()
    pengirim = (data.get('pengirim') or '').strip().rstrip(',').strip()
    perihal = (data.get('perihal') or '').strip()
    kategori_nama = (data.get('kategori') or 'Umum').strip() or 'Umum'

    if not nomor or not pengirim or not perihal:
        return {'saved': False, 'message': 'Nomor, pengirim, dan perihal wajib diisi.'}

    tanggal_str = (data.get('tanggal') or '').strip()
    if tanggal_str:
        try:
            tgl_obj = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
        except ValueError:
            tgl_obj = datetime.now().date()
    else:
        tgl_obj = datetime.now().date()

    existing_nomor = Surat.query.filter(Surat.nomor_surat == nomor, Surat.id != surat.id).first()
    if existing_nomor:
        return {'saved': False, 'message': f'Nomor surat {nomor} sudah ada di arsip.'}

    kat = _get_or_create_kategori(kategori_nama)
    file_path = surat.file_path
    if file_storage is not None and getattr(file_storage, 'filename', None):
        if surat.file_path and surat.file_path != 'static/uploads/surat_baru.pdf':
            _delete_surat_file(surat.file_path)
        file_path = _save_uploaded_surat_file(file_storage)
    elif data.get('file_path'):
        file_path = _normalize_surat_file_path(data.get('file_path'))
    elif data.get('file'):
        file_path = _normalize_surat_file_path(data.get('file'))

    surat.nomor_surat = nomor
    surat.tanggal_surat = tgl_obj
    surat.pengirim = pengirim
    surat.perihal = perihal
    surat.kategori_id = kat.id
    surat.file_path = file_path
    db.session.commit()

    if user_id:
        log_aktivitas(user_id, f'Mengubah surat: {nomor}', 'Selesai')

    return {'saved': True, 'message': 'Surat berhasil diperbarui.'}


def _send_surat_file(surat, as_attachment=False):
    file_path = _normalize_surat_file_path(surat.file_path)
    abs_path = os.path.join(app.root_path, *file_path.split('/'))
    if not os.path.isfile(abs_path):
        abort(404, description='File surat tidak ditemukan di server.')
    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    response = make_response(send_from_directory(
        directory,
        filename,
        mimetype='application/pdf',
        as_attachment=as_attachment,
        download_name=filename if as_attachment else None,
    ))
    disposition = 'attachment' if as_attachment else 'inline'
    response.headers['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def _serialize_surat(s):
    kategori_nama = s.kategori_rel.nama if s.kategori_rel else 'Lainnya'
    file_path = _normalize_surat_file_path(s.file_path)
    return {
        'id': s.id,
        'nomor': s.nomor_surat,
        'tanggal': s.tanggal_surat.strftime('%Y-%m-%d'),
        'pengirim': s.pengirim,
        'perihal': s.perihal,
        'kategori': kategori_nama,
        'file': file_path,
        'file_path': file_path,
        'created_at': s.created_at.isoformat() if s.created_at else None,
    }


@app.route('/letters', methods=['GET'])
@login_required
def get_letters_api():
    if current_user.role != 'Admin':
        return jsonify({'status': 'error', 'message': 'Akses ditolak.'}), 403
    surat_list = Surat.query.order_by(Surat.created_at.desc()).all()
    return jsonify([_serialize_surat(s) for s in surat_list])


@app.route('/letters/<int:surat_id>', methods=['GET'])
@login_required
def get_letter_detail_api(surat_id):
    surat = Surat.query.get_or_404(surat_id)
    return jsonify(_serialize_surat(surat))


@app.route('/letters', methods=['POST'])
@login_required
def create_letter_api():
    if current_user.role != 'Admin':
        return jsonify({'status': 'error', 'message': 'Akses ditolak.'}), 403

    payload = request.get_json(silent=True) or {}
    if not payload and request.form:
        payload = request.form.to_dict()

    file_storage = request.files.get('file') if request.files else None
    result = _create_surat_from_payload(payload, user_id=current_user.id, file_storage=file_storage)
    if result['saved']:
        flash('Surat berhasil disimpan.', 'success')
        return jsonify({'status': 'success', 'message': result['message']})
    flash(result['message'], 'error')
    return jsonify({'status': 'error', 'message': result['message']})


@app.route('/letters/<int:surat_id>', methods=['PATCH', 'PUT'])
@login_required
def update_letter_api(surat_id):
    if current_user.role != 'Admin':
        return jsonify({'status': 'error', 'message': 'Akses ditolak.'}), 403

    surat = Surat.query.get_or_404(surat_id)
    payload = request.get_json(silent=True) or {}
    if not payload and request.form:
        payload = request.form.to_dict()

    file_storage = request.files.get('file') if request.files else None
    result = _update_surat_from_payload(surat, payload, user_id=current_user.id, file_storage=file_storage)
    if result['saved']:
        flash('Surat berhasil diperbarui.', 'success')
        return jsonify({'status': 'success', 'message': result['message']})
    flash(result['message'], 'error')
    return jsonify({'status': 'error', 'message': result['message']})


@app.route('/letters/<int:surat_id>', methods=['DELETE'])
@login_required
def delete_letter_api(surat_id):
    if current_user.role != 'Admin':
        return jsonify({'status': 'error', 'message': 'Akses ditolak.'}), 403

    surat = Surat.query.get_or_404(surat_id)
    nomor_surat = surat.nomor_surat
    if surat.file_path:
        _delete_surat_file(surat.file_path)
    db.session.delete(surat)
    db.session.commit()
    log_aktivitas(current_user.id, f'Menghapus surat: {nomor_surat}', 'Selesai')
    flash('Surat berhasil dihapus.', 'success')
    return jsonify({'status': 'success', 'message': 'Surat berhasil dihapus.'})


@app.route("/api/surat", methods=["GET"])
@login_required
def get_surat_api():
    surat_list = Surat.query.order_by(Surat.created_at.desc()).all()
    return jsonify([_serialize_surat(s) for s in surat_list])


@app.route("/api/surat/sync", methods=["GET"])
@login_required
def surat_sync_api():
    """Endpoint ringan untuk polling perubahan arsip surat antar dashboard."""
    latest = Surat.query.order_by(Surat.created_at.desc()).first()
    return jsonify({
        "count": Surat.query.count(),
        "latest_id": latest.id if latest else 0,
        "latest_at": latest.created_at.isoformat() if latest and latest.created_at else None,
    })

@app.route("/api/surat/add", methods=["POST"])
@login_required
def add_surat_api():
    payload = request.get_json(silent=True) or {}
    if not payload and request.form:
        payload = request.form.to_dict()
    file_storage = request.files.get('file') if request.files else None
    try:
        result = _create_surat_from_payload(payload, user_id=current_user.id, file_storage=file_storage)
        if result['saved']:
            return jsonify({"status": "success", "message": result['message']})
        return jsonify({"status": "error", "message": result['message']})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/surat/edit/<int:id>", methods=["PUT", "PATCH"])
@login_required
def edit_surat_api(id):
    surat = Surat.query.get(id)
    if surat:
        try:
            payload = request.get_json(silent=True) or {}
            if not payload and request.form:
                payload = request.form.to_dict()
            file_storage = request.files.get('file') if request.files else None
            result = _update_surat_from_payload(surat, payload, user_id=current_user.id, file_storage=file_storage)
            if result['saved']:
                return jsonify({"status": "success", "message": result['message']})
            return jsonify({"status": "error", "message": result['message']})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Surat tidak ditemukan"})

@app.route("/api/surat/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_surat_api(id):
    surat = Surat.query.get(id)
    if surat:
        nomor_surat = surat.nomor_surat
        if surat.file_path:
            _delete_surat_file(surat.file_path)
        db.session.delete(surat)
        db.session.commit()
        log_aktivitas(current_user.id, f"Menghapus surat: {nomor_surat}", "Selesai")
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Surat tidak ditemukan"})


@app.route("/api/surat/view/<int:id>")
@login_required
def view_surat_file(id):
    """Buka file PDF surat langsung di browser."""
    surat = Surat.query.get_or_404(id)
    return _send_surat_file(surat, as_attachment=False)


@app.route("/api/surat/download/<int:id>")
@login_required
def download_surat_file(id):
    """Unduh file PDF surat."""
    surat = Surat.query.get_or_404(id)
    return _send_surat_file(surat, as_attachment=True)


@app.route('/laporan_arsip/export/excel')
@login_required
def export_laporan_excel():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))

    query = Surat.query
    kategori_filter = (request.args.get('kategori') or '').strip()
    start_date = (request.args.get('start_date') or '').strip()
    end_date = (request.args.get('end_date') or '').strip()
    keyword = (request.args.get('keyword') or '').strip()

    if kategori_filter:
        query = query.join(Kategori).filter(Kategori.nama == kategori_filter)
    if start_date:
        query = query.filter(Surat.tanggal_surat >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Surat.tanggal_surat <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if keyword:
        like_value = f'%{keyword}%'
        query = query.filter(or_(Surat.nomor_surat.ilike(like_value), Surat.pengirim.ilike(like_value), Surat.perihal.ilike(like_value)))

    surat_list = query.order_by(Surat.tanggal_surat.desc(), Surat.created_at.desc()).all()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Laporan Arsip'
    sheet.append(['Nomor Surat', 'Tanggal', 'Pengirim', 'Perihal', 'Kategori'])
    for surat in surat_list:
        sheet.append([surat.nomor_surat, surat.tanggal_surat.strftime('%Y-%m-%d'), surat.pengirim, surat.perihal, surat.kategori_rel.nama if surat.kategori_rel else 'Lainnya'])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=laporan_arsip.xlsx'
    return response


@app.route('/laporan_arsip/export/pdf')
@login_required
def export_laporan_pdf():
    if current_user.role != 'Admin':
        return redirect(url_for('dashboard_karyawan'))

    # ── Ambil filter dari query string ────────────────────────────────────────
    query = Surat.query
    kategori_filter = (request.args.get('kategori') or '').strip()
    start_date_str   = (request.args.get('start_date') or '').strip()
    end_date_str     = (request.args.get('end_date') or '').strip()
    keyword          = (request.args.get('keyword') or '').strip()

    if kategori_filter:
        query = query.join(Kategori).filter(Kategori.nama == kategori_filter)
    if start_date_str:
        query = query.filter(Surat.tanggal_surat >= datetime.strptime(start_date_str, '%Y-%m-%d').date())
    if end_date_str:
        query = query.filter(Surat.tanggal_surat <= datetime.strptime(end_date_str, '%Y-%m-%d').date())
    if keyword:
        like_val = f'%{keyword}%'
        query = query.filter(or_(
            Surat.nomor_surat.ilike(like_val),
            Surat.pengirim.ilike(like_val),
            Surat.perihal.ilike(like_val),
        ))

    surat_list = query.order_by(Surat.tanggal_surat.desc(), Surat.created_at.desc()).all()

    # ── Generate PDF dengan ReportLab ────────────────────────────────────────
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    # ── Warna & Style ─────────────────────────────────────────────────────────
    COLOR_HEADER_BG  = colors.HexColor('#1e3a5f')   # biru tua
    COLOR_HEADER_FG  = colors.white
    COLOR_ROW_ALT    = colors.HexColor('#f0f4fa')   # biru muda untuk baris genap
    COLOR_ACCENT     = colors.HexColor('#3b82f6')   # biru aksen
    COLOR_TEXT       = colors.HexColor('#1f2937')
    COLOR_MUTED      = colors.HexColor('#6b7280')
    COLOR_BORDER     = colors.HexColor('#d1d5db')

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=18,
        textColor=COLOR_HEADER_BG,
        spaceAfter=4,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
    )
    style_subtitle = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_MUTED,
        spaceAfter=2,
        alignment=TA_CENTER,
    )
    style_info = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=8.5,
        textColor=COLOR_TEXT,
        spaceAfter=2,
    )
    style_cell = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_TEXT,
        leading=11,
    )
    style_cell_center = ParagraphStyle(
        'CellCenter',
        parent=style_cell,
        alignment=TA_CENTER,
    )

    story = []

    # ── Header Laporan ────────────────────────────────────────────────────────
    story.append(Paragraph('LAPORAN ARSIP SURAT', style_title))
    story.append(Paragraph('Sistem Manajemen Arsip Digital — DigiSurat', style_subtitle))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=2, color=COLOR_ACCENT, spaceAfter=6))

    # ── Info filter & metadata ────────────────────────────────────────────────
    cetak_waktu = datetime.now().strftime('%d %B %Y, %H:%M WIB')
    filter_parts = []
    if kategori_filter:
        filter_parts.append(f'Kategori: {kategori_filter}')
    if start_date_str:
        filter_parts.append(f'Dari: {datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d %b %Y")}')
    if end_date_str:
        filter_parts.append(f'Sampai: {datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d %b %Y")}')
    if keyword:
        filter_parts.append(f'Kata Kunci: {keyword}')
    filter_text = ' | '.join(filter_parts) if filter_parts else 'Semua Data'

    meta_data = [
        [Paragraph(f'<b>Dicetak pada:</b> {cetak_waktu}', style_info),
         Paragraph(f'<b>Filter:</b> {filter_text}', style_info),
         Paragraph(f'<b>Total Data:</b> {len(surat_list)} surat', style_info)],
    ]
    meta_table = Table(meta_data, colWidths=['35%', '40%', '25%'])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # ── Baris Header Tabel ────────────────────────────────────────────────────
    table_header = [
        Paragraph('<b>No</b>', style_cell_center),
        Paragraph('<b>Nomor Surat</b>', style_cell_center),
        Paragraph('<b>Tanggal Surat</b>', style_cell_center),
        Paragraph('<b>Pengirim</b>', style_cell_center),
        Paragraph('<b>Perihal</b>', style_cell_center),
        Paragraph('<b>Kategori</b>', style_cell_center),
    ]

    # ── Baris Data Tabel ─────────────────────────────────────────────────────
    table_data = [table_header]
    for idx, surat in enumerate(surat_list, start=1):
        kat_nama = surat.kategori_rel.nama if surat.kategori_rel else 'Lainnya'
        row = [
            Paragraph(str(idx), style_cell_center),
            Paragraph(surat.nomor_surat or '-', style_cell),
            Paragraph(surat.tanggal_surat.strftime('%d-%m-%Y'), style_cell_center),
            Paragraph(surat.pengirim or '-', style_cell),
            Paragraph(surat.perihal or '-', style_cell),
            Paragraph(kat_nama, style_cell_center),
        ]
        table_data.append(row)

    if not surat_list:
        table_data.append([
            Paragraph('', style_cell),
            Paragraph('Tidak ada data yang sesuai dengan filter yang dipilih.', style_cell),
            Paragraph('', style_cell),
            Paragraph('', style_cell),
            Paragraph('', style_cell),
            Paragraph('', style_cell),
        ])

    # ── Lebar kolom (total ≈ landscape A4 - margin = ~26 cm) ─────────────────
    col_widths = [1.2*cm, 5.5*cm, 3.0*cm, 5.5*cm, 8.0*cm, 3.3*cm]

    arsip_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # ── Style Tabel ───────────────────────────────────────────────────────────
    tbl_style = TableStyle([
        # Header
        ('BACKGROUND',   (0, 0), (-1, 0), COLOR_HEADER_BG),
        ('TEXTCOLOR',    (0, 0), (-1, 0), COLOR_HEADER_FG),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 8.5),
        ('ROWPADDING',   (0, 0), (-1, 0), 8),
        ('ALIGN',        (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN',       (0, 0), (-1, 0), 'MIDDLE'),
        # Data rows
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 8),
        ('ROWPADDING',   (0, 1), (-1, -1), 6),
        ('VALIGN',       (0, 1), (-1, -1), 'MIDDLE'),
        # Grid
        ('GRID',         (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LINEBELOW',    (0, 0), (-1, 0), 1.5, COLOR_ACCENT),
    ])
    # Warna baris zebra (selang-seling)
    for row_idx in range(1, len(table_data)):
        if row_idx % 2 == 0:
            tbl_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), COLOR_ROW_ALT)

    arsip_table.setStyle(tbl_style)
    story.append(arsip_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width='100%', thickness=0.5, color=COLOR_BORDER))
    story.append(Spacer(1, 4))
    style_footer = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7.5,
        textColor=COLOR_MUTED,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        f'DigiSurat — Sistem Manajemen Arsip Digital &nbsp;|&nbsp; '
        f'Dokumen ini digenerate otomatis pada {cetak_waktu} &nbsp;|&nbsp; '
        f'Total {len(surat_list)} data arsip surat',
        style_footer,
    ))

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=laporan_arsip.pdf'
    return response

# ======================
# API MANAJEMEN KATEGORI
# ======================

@app.route("/api/kategori", methods=["GET"])
@login_required
def get_kategori_api():
    kategori_list = Kategori.query.all()
    output = []
    for k in kategori_list:
        output.append({
            "id": k.id,
            "nama": k.nama,
            "deskripsi": k.deskripsi
        })
    return jsonify(output)

@app.route("/api/kategori/add", methods=["POST"])
@login_required
def add_kategori_api():
    data = request.json
    try:
        new_kategori = Kategori(
            nama=data['nama'],
            deskripsi=data.get('deskripsi', '')
        )
        db.session.add(new_kategori)
        db.session.commit()
        log_aktivitas(current_user.id, f"Menambahkan kategori: {data['nama']}", "Selesai")
        return jsonify({"status": "success", "message": "Kategori berhasil ditambah"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/kategori/edit/<int:id>", methods=["PUT"])
@login_required
def edit_kategori_api(id):
    data = request.json
    kat = Kategori.query.get(id)
    if kat:
        try:
            kat.nama = data['nama']
            kat.deskripsi = data.get('deskripsi', '')
            db.session.commit()
            log_aktivitas(current_user.id, f"Mengubah kategori: {data['nama']}", "Selesai")
            return jsonify({"status": "success", "message": "Kategori berhasil diperbarui"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Kategori tidak ditemukan"})

@app.route("/api/kategori/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_kategori_api(id):
    kat = Kategori.query.get(id)
    if kat:
        try:
            surat_count = Surat.query.filter_by(kategori_id=id).count()
            if surat_count > 0:
                return jsonify({"status": "error", "message": "Gagal: Kategori masih digunakan oleh arsip surat."})
            
            nama_kat = kat.nama
            db.session.delete(kat)
            db.session.commit()
            log_aktivitas(current_user.id, f"Menghapus kategori: {nama_kat}", "Selesai")
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Kategori tidak ditemukan"})



# ======================
# API PENGATURAN AI (ML Pipeline)
# ======================

ALLOWED_DATASET_EXT = {'.csv', '.xlsx', '.xls', '.json'}


def admin_required_api():
    if not current_user.is_authenticated or current_user.role != 'Admin':
        return jsonify({"status": "error", "message": "Akses ditolak. Hanya Admin."}), 403
    return None


@app.route("/api/ai/status", methods=["GET"])
@login_required
def ai_status():
    return jsonify({"status": "success", **ai_engine.get_status()})


@app.route("/api/ai/config", methods=["GET"])
@login_required
def ai_get_config():
    return jsonify({"status": "success", "config": ai_engine.get_config()})


@app.route("/api/ai/config", methods=["POST"])
@login_required
def ai_save_config():
    denied = admin_required_api()
    if denied:
        return denied

    data = request.json or {}
    active_param = data.get('active_param')
    if not active_param:
        return jsonify({"status": "error", "message": "Pilih satu parameter aktif terlebih dahulu."}), 400

    vectorizer_map = {
        'TF-IDF - Sangat Disarankan': 'tfidf',
        'tfidf': 'tfidf',
        'Count Vectorizer': 'count',
        'count': 'count',
        'Bag of Words': 'bow',
        'bow': 'bow',
    }
    metric_map = {
        'Euclidean Distance (standar)': 'euclidean',
        'euclidean': 'euclidean',
        'Manhattan Distance': 'manhattan',
        'manhattan': 'manhattan',
        'Cosine Distance': 'cosine',
        'cosine': 'cosine',
    }

    values = {}
    if active_param == 'preprocessing':
        values['vectorizer'] = vectorizer_map.get(data.get('vectorizer'), data.get('vectorizer', 'tfidf'))
    elif active_param == 'knn':
        values['knn_k'] = int(data.get('knn_k', 11))
        values['knn_metric'] = metric_map.get(data.get('knn_metric'), data.get('knn_metric', 'euclidean'))
    elif active_param == 'naive_bayes':
        values['nb_alpha'] = float(data.get('nb_alpha', 1.0))
    else:
        return jsonify({"status": "error", "message": "Parameter aktif tidak valid."}), 400

    try:
        saved = ai_engine.save_active_param_config(active_param, values)
        label_map = {
            'preprocessing': 'Pre-Processing',
            'knn': 'K-NN',
            'naive_bayes': 'Naive Bayes',
        }
        return jsonify({
            "status": "success",
            "message": f"Konfigurasi {label_map[active_param]} disimpan",
            "config": saved,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/ai/train", methods=["POST"])
@login_required
def ai_train():
    denied = admin_required_api()
    if denied:
        return denied

    if 'dataset' not in request.files:
        return jsonify({"status": "error", "message": "File dataset wajib diunggah."}), 400

    file = request.files['dataset']
    if not file or not file.filename:
        return jsonify({"status": "error", "message": "File dataset tidak valid."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_DATASET_EXT:
        return jsonify({"status": "error", "message": "Format tidak didukung. Gunakan CSV, XLSX, atau JSON."}), 400

    os.makedirs(ai_engine.DATASETS_DIR, exist_ok=True)
    filename = secure_filename(file.filename)
    save_path = os.path.join(ai_engine.DATASETS_DIR, filename)
    file.save(save_path)

    active_param = (request.form.get('active_param') or '').strip()
    if active_param not in ai_engine.VALID_ACTIVE_PARAMS:
        return jsonify({
            "status": "error",
            "message": "Pilih satu parameter aktif (Pre-Processing, K-NN, atau Naive Bayes) sebelum melatih.",
        }), 400

    try:
        ai_engine.update_config({}, active_param=active_param)
        config = ai_engine.get_config()
        metadata = ai_engine.train_models(save_path, config, target=active_param)
        label_map = {
            'preprocessing': 'Pre-Processing (Naive Bayes & K-NN)',
            'knn': 'K-NN',
            'naive_bayes': 'Naive Bayes',
        }
        trained_label = label_map.get(active_param, active_param)
        return jsonify({
            "status": "success",
            "message": f"Pelatihan {trained_label} berhasil. Model .pkl tersimpan.",
            "last_trained": metadata['last_trained'],
            "total_samples": metadata['total_samples'],
            "metrics": metadata['metrics'],
            "best_model": metadata['best_model'],
            "trained_target": metadata.get('last_trained_target', []),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/ai/classify", methods=["POST"])
@login_required
def ai_classify():
    data = request.json or {}
    perihal = (data.get('perihal') or '').strip()
    pengirim = (data.get('pengirim') or '').strip()
    text = f"{pengirim} {perihal}".strip() or perihal

    if not text:
        return jsonify({"status": "error", "message": "Perihal atau pengirim wajib diisi."}), 400

    result = ai_engine.classify_text(text)
    if result.get('status') == 'error':
        return jsonify(result), 400
    return jsonify(result)


# ── PROFIL USER ──────────────────────────────────────────────────────────────

@app.route("/api/profile/stats", methods=["GET"])
@login_required
def profile_stats():
    """Stat card di halaman profil: total surat, algoritma aktif, akurasi."""
    try:
        total_surat = Surat.query.count()
        jumlah_kategori = Kategori.query.count()
        ai_status   = ai_engine.get_status()
        nb  = (ai_status.get('metrics') or {}).get('naive_bayes', {})
        knn = (ai_status.get('metrics') or {}).get('knn', {})
        best_acc  = max(nb.get('accuracy', 0), knn.get('accuracy', 0))
        algo_name = ai_status.get('best_model', '').upper() or '-'
        if algo_name == 'NAIVE_BAYES':
            algo_name = 'Naive Bayes'
        elif algo_name == 'KNN':
            algo_name = 'K-NN'

        if ai_status.get('last_prediction_confidence') is not None:
            akurasi_str = f"{ai_status['last_prediction_confidence']}%"
        else:
            akurasi_str = f"{best_acc*100:.0f}%" if ai_status.get('trained') else '-'

        return jsonify({
            "total_surat": total_surat,
            "jumlah_kategori": jumlah_kategori,
            "algoritma":   algo_name if ai_status.get('trained') else '-',
            "akurasi":     akurasi_str,
        })
    except Exception as e:
        return jsonify({"total_surat": 0, "jumlah_kategori": 0, "algoritma": "-", "akurasi": "-"})




@app.route("/api/surat/upload-pdf", methods=["POST"])
@login_required
def upload_pdf_api():
    """Terima PDF, ekstrak field surat otomatis menggunakan AI."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "File PDF wajib diunggah."}), 400

    file = request.files['file']
    if not file or not file.filename:
        return jsonify({"status": "error", "message": "File tidak valid."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != '.pdf':
        return jsonify({"status": "error", "message": "Hanya file PDF yang didukung."}), 400

    # Simpan PDF sementara ke folder uploads
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(file.filename)
    save_path = os.path.join(upload_folder, filename)
    file.save(save_path)

    # Ekstrak field dari PDF
    fields = ai_engine.extract_pdf_fields(save_path)
    file_path = _normalize_surat_file_path(filename)
    
    if fields.get('confidence'):
        metadata = ai_engine.load_metadata()
        metadata['last_prediction_confidence'] = fields['confidence']
        ai_engine.save_metadata(metadata)

    return jsonify({
        "status": "success",
        "readable": fields['readable'],
        "nomor":    fields['nomor'],
        "tanggal":  fields['tanggal'],
        "pengirim": fields['pengirim'],
        "perihal":  fields['perihal'],
        "kategori": fields['kategori'],
        "model":    fields['model'],
        "confidence": fields['confidence'],
        "file":     file_path,
        "saved":    False,
        "save_message": "",
        "surat_id": None,
    })


# ======================
# SCRIPT UNTUK MEMBUAT DATABASE (Hanya jalan sekali di awal)
# ======================
def create_initial_data():
    with app.app_context():
        db.create_all() 
        if not User.query.filter_by(role='Admin').first():
            admin = User(nama="Administrator", email="admin@polibatam.ac.id", password=generate_password_hash("admin123"), role="Admin")
            db.session.add(admin)
        if not User.query.filter_by(role='Karyawan').first():
            karyawan = User(nama="Karyawan Biasa", email="karyawan@polibatam.ac.id", password=generate_password_hash("karyawan123"), role="Karyawan")
            db.session.add(karyawan)
        
        if not Kategori.query.first():
            k1 = Kategori(nama="Undangan", deskripsi="Surat Undangan")
            k2 = Kategori(nama="Pemberitahuan", deskripsi="Surat Pemberitahuan")
            k3 = Kategori(nama="Keputusan", deskripsi="Surat Keputusan")
            db.session.add_all([k1, k2, k3])

        db.session.commit()
        print("Database berhasil dibuat & Akun/Kategori default disuntikkan!")

if __name__ == "__main__":
    create_initial_data()
    app.run(debug=True)