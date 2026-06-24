from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, send_from_directory, abort, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Kategori, Surat, AktivitasLog # Import database dari models.py
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import ai_engine
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_digisurat_2026' # Wajib ada untuk flash message/session

# Konfigurasi Database (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digisurat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    return render_template("manajemen_surat.html")

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
    return render_template("laporan_arsip.html")

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
# API MANAJEMEN SURAT (CRUD KE MYSQL)
# ======================

def _normalize_surat_file_path(file_value):
    if not file_value:
        return 'static/uploads/surat_baru.pdf'
    file_value = str(file_value).replace('\\', '/').strip()
    if file_value.startswith('static/uploads/'):
        return file_value
    return f'static/uploads/{os.path.basename(file_value)}'


def _send_surat_file(surat, as_attachment=False):
    file_path = _normalize_surat_file_path(surat.file_path)
    abs_path = os.path.join(app.root_path, file_path.replace('/', os.sep))
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
    kategori_nama = s.kategori_rel.nama if s.kategori_rel else "Lainnya"
    file_path = _normalize_surat_file_path(s.file_path)
    return {
        "id": s.id,
        "nomor": s.nomor_surat,
        "tanggal": s.tanggal_surat.strftime("%Y-%m-%d"),
        "pengirim": s.pengirim,
        "perihal": s.perihal,
        "kategori": kategori_nama,
        "file": file_path,
        "file_path": file_path,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


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
    data = request.json
    try:
        kategori_nama = data.get('kategori', 'Umum')
        kat = Kategori.query.filter_by(nama=kategori_nama).first()
        if not kat:
            kat = Kategori(nama=kategori_nama)
            db.session.add(kat)
            db.session.commit()
            
        tgl_str = data['tanggal'] # expected YYYY-MM-DD
        from datetime import datetime
        tgl_obj = datetime.strptime(tgl_str, '%Y-%m-%d').date()

        new_surat = Surat(
            nomor_surat=data['nomor'],
            tanggal_surat=tgl_obj,
            pengirim=data['pengirim'],
            perihal=data['perihal'],
            file_path=_normalize_surat_file_path(data.get('file', 'surat_baru.pdf')),
            kategori_id=kat.id
        )
        db.session.add(new_surat)
        db.session.commit()
        log_aktivitas(current_user.id, f"Menambahkan surat: {data['nomor']}", "Selesai")
        return jsonify({"status": "success", "message": "Surat berhasil ditambah"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/surat/edit/<int:id>", methods=["PUT"])
@login_required
def edit_surat_api(id):
    data = request.json
    surat = Surat.query.get(id)
    if surat:
        try:
            kategori_nama = data.get('kategori', 'Umum')
            kat = Kategori.query.filter_by(nama=kategori_nama).first()
            if not kat:
                kat = Kategori(nama=kategori_nama)
                db.session.add(kat)
                db.session.commit()
            
            tgl_str = data['tanggal']
            from datetime import datetime
            tgl_obj = datetime.strptime(tgl_str, '%Y-%m-%d').date()

            surat.nomor_surat = data['nomor']
            surat.tanggal_surat = tgl_obj
            surat.pengirim = data['pengirim']
            surat.perihal = data['perihal']
            surat.kategori_id = kat.id
            if 'file' in data and data['file']:
                surat.file_path = _normalize_surat_file_path(data['file'])
            
            db.session.commit()
            log_aktivitas(current_user.id, f"Mengubah surat: {data['nomor']}", "Selesai")
            return jsonify({"status": "success", "message": "Surat berhasil diperbarui"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Surat tidak ditemukan"})

@app.route("/api/surat/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_surat_api(id):
    surat = Surat.query.get(id)
    if surat:
        nomor_surat = surat.nomor_surat
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
        ai_status   = ai_engine.get_ai_status()
        nb  = (ai_status.get('metrics') or {}).get('naive_bayes', {})
        knn = (ai_status.get('metrics') or {}).get('knn', {})
        best_acc  = max(nb.get('accuracy', 0), knn.get('accuracy', 0))
        algo_name = ai_status.get('best_model', '').upper() or '-'
        if algo_name == 'NAIVE_BAYES':
            algo_name = 'Naive Bayes'
        elif algo_name == 'KNN':
            algo_name = 'K-NN'

        return jsonify({
            "total_surat": total_surat,
            "jumlah_kategori": jumlah_kategori,
            "algoritma":   algo_name if ai_status.get('trained') else '-',
            "akurasi":     f"{best_acc*100:.0f}%" if ai_status.get('trained') else '-',
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
        "file":     _normalize_surat_file_path(filename),
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