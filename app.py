from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Kategori, Surat # Import database dari models.py
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia_digisurat_2026' # Wajib ada untuk flash message/session

# Konfigurasi Database (MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/digisurat_db'
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
    if user and user.password == password:
        login_user(user) # Daftarkan sesi user
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
    logout_user() # Hapus sesi user
    return redirect(url_for("index"))

# ======================
# MENU ADMIN (Terproteksi)
# ======================
@app.route("/dashboard_admin")
@login_required
def dashboard_admin():
    return render_template("dashboard_admin.html")

@app.route("/manajemen_surat")
@login_required
def manajemen_surat():
    return render_template("manajemen_surat.html")

@app.route("/kategori_surat")
@login_required
def kategori_surat():
    return render_template("kategori_surat.html")

@app.route("/laporan_arsip")
@login_required
def laporan_arsip():
    return render_template("laporan_arsip.html")

@app.route("/manajemen_user")
@login_required
def manajemen_user():
    return render_template("manajemen_user.html")

@app.route("/pengaturan_ai")
@login_required
def pengaturan_ai():
    return render_template("pengaturan_ai.html")

@app.route("/perbandingan_algoritma")
@login_required
def perbandingan_algoritma():
    return render_template("perbandingan_algoritma.html")

@app.route("/pengaturan_akun_admin")
@login_required
def pengaturan_akun_admin():
    return render_template("pengaturan_akun_admin.html")

# ======================
# MENU KARYAWAN (Terproteksi)
# ======================
@app.route("/dashboard_karyawan")
@login_required
def dashboard_karyawan():
    return render_template("dashboard_karyawan.html")

@app.route("/pengaturan_akun")
@login_required
def pengaturan_akun():
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
        })
    return jsonify(output)

@app.route("/api/users/add", methods=["POST"])
@login_required
def add_user():
    data = request.json
    try:
        new_user = User(
            nama=data['nama'],
            email=data['email'],
            password='digisurat123', # Password default
            role=data['role'],
        )
        db.session.add(new_user)
        db.session.commit()
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
            user.nama = data['nama']
            user.email = data['email']
            user.role = data['role']
            db.session.commit()
            return jsonify({"status": "success", "message": "User berhasil diperbarui"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "User tidak ditemukan"})

@app.route("/api/users/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_user_api(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
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
    if current_user.password == old_pass:
        current_user.password = new_pass
        db.session.commit()
        return jsonify({"status": "success", "message": "Password berhasil diperbarui"})
    else:
        return jsonify({"status": "error", "message": "Password lama tidak sesuai"})


# ======================
# API MANAJEMEN SURAT (CRUD KE MYSQL)
# ======================

@app.route("/api/surat", methods=["GET"])
@login_required
def get_surat_api():
    surat_list = Surat.query.order_by(Surat.created_at.desc()).all()
    output = []
    for s in surat_list:
        kategori_nama = s.kategori_rel.nama if s.kategori_rel else "Lainnya"
        output.append({
            "id": s.id,
            "nomor": s.nomor_surat,
            "tanggal": s.tanggal_surat.strftime("%Y-%m-%d"),
            "pengirim": s.pengirim,
            "perihal": s.perihal,
            "kategori": kategori_nama,
            "file": s.file_path
        })
    return jsonify(output)

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
            file_path=data.get('file', 'surat_baru.pdf'),
            kategori_id=kat.id
        )
        db.session.add(new_surat)
        db.session.commit()
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
                surat.file_path = data['file']
            
            db.session.commit()
            return jsonify({"status": "success", "message": "Surat berhasil diperbarui"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Surat tidak ditemukan"})

@app.route("/api/surat/delete/<int:id>", methods=["DELETE"])
@login_required
def delete_surat_api(id):
    surat = Surat.query.get(id)
    if surat:
        db.session.delete(surat)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Surat tidak ditemukan"})

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
            
            db.session.delete(kat)
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Kategori tidak ditemukan"})



# ======================
# SCRIPT UNTUK MEMBUAT DATABASE (Hanya jalan sekali di awal)
# ======================
def create_initial_data():
    with app.app_context():
        db.create_all() 
        if not User.query.filter_by(email='admin@polibatam.ac.id').first():
            admin = User(nama="Administrator", email="admin@polibatam.ac.id", password="admin123", role="Admin")
            karyawan = User(nama="Karyawan Biasa", email="karyawan@polibatam.ac.id", password="karyawan123", role="Karyawan")
            db.session.add_all([admin, karyawan])
        
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