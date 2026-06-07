from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Kategori, Surat # Import database dari models.py
from werkzeug.utils import secure_filename
import ai_engine
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