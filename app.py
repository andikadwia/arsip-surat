from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Kategori, Surat # Import database dari models.py
import os

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
# SCRIPT UNTUK MEMBUAT DATABASE (Hanya jalan sekali di awal)
# ======================
def create_initial_data():
    with app.app_context():
        db.create_all() 
        if not User.query.filter_by(email='admin@polibatam.ac.id').first():
            admin = User(nama="Administrator", email="admin@polibatam.ac.id", password="admin123", role="Admin")
            karyawan = User(nama="Karyawan Biasa", email="karyawan@polibatam.ac.id", password="karyawan123", role="Karyawan")
            db.session.add_all([admin, karyawan])
            db.session.commit()
            print("Database berhasil dibuat & Akun default disuntikkan!")

if __name__ == "__main__":
    create_initial_data()
    app.run(debug=True)