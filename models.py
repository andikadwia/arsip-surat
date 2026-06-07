from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin  # <-- INI YANG PALING PENTING
from datetime import datetime

db = SQLAlchemy()

# Perhatikan di dalam kurung: (UserMixin, db.Model)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) 
    role = db.Column(db.String(20), nullable=False, default='Karyawan')
    foto = db.Column(db.String(255), nullable=True)
    aktivitas = db.relationship('AktivitasLog', backref='user', lazy=True, cascade='all, delete-orphan')

class Kategori(db.Model):
    __tablename__ = 'kategori'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text)
    surat = db.relationship('Surat', backref='kategori_rel', lazy=True)

class Surat(db.Model):
    __tablename__ = 'surat'
    
    id = db.Column(db.Integer, primary_key=True)
    nomor_surat = db.Column(db.String(100), unique=True, nullable=False)
    tanggal_surat = db.Column(db.Date, nullable=False)
    pengirim = db.Column(db.String(150), nullable=False)
    perihal = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    kategori_id = db.Column(db.Integer, db.ForeignKey('kategori.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AktivitasLog(db.Model):
    __tablename__ = 'aktivitas_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kegiatan = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Sukses')  # Sukses, Selesai, Info
    waktu = db.Column(db.DateTime, default=datetime.utcnow)