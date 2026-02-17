import sqlite3
import os

DB_NAME = 'db_arsip.sqlite'

def buat_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("Database lama di-reset...")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabel Arsip Surat
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS arsip_surat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        no_surat TEXT,
        pengirim TEXT,
        isi_surat TEXT,
        kategori_manual TEXT,
        prediksi_nb TEXT,
        prediksi_knn TEXT,
        tanggal_input TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    # Data Dummy
    cursor.execute("INSERT INTO arsip_surat (no_surat, pengirim, isi_surat, kategori_manual) VALUES ('001', 'Rektor', 'Rapat senat', 'Undangan')")
    
    conn.commit()
    conn.close()
    print("DATABASE BERHASIL DIBUAT: db_arsip.sqlite")

if __name__ == '__main__':
    buat_database()
