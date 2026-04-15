/* ============================================================
   DigiSurat - Shared Data Store (localStorage)
   ============================================================ */

// --- Letters (Surat) ---
const LETTERS_KEY = 'digisurat_letters';
const KATEGORI_KEY = 'digisurat_kategori';
const USERS_KEY = 'digisurat_users';

const defaultLetters = [
  {
    id: 1,
    nomor: '420/123/Disdik-SB/IV/2026',
    tanggal: '10-04-2026',
    pengirim: 'Dinas Pendidikan Sumatera Barat',
    perihal: 'Undangan Rapat Koordinasi Pendidikan',
    kategori: 'Undangan',
    file: 'undangan_rapat.pdf'
  },
  {
    id: 2,
    nomor: '001/PKB/III/2026',
    tanggal: '08-03-2026',
    pengirim: 'Politeknik Batam',
    perihal: 'Pemberitahuan Jadwal Ujian Akhir Semester',
    kategori: 'Pemberitahuan',
    file: 'pemberitahuan_uas.pdf'
  },
  {
    id: 3,
    nomor: 'SK-042/DIR/II/2026',
    tanggal: '15-02-2026',
    pengirim: 'Direktur Politeknik Batam',
    perihal: 'Keputusan Pengangkatan Dosen Koordinator',
    kategori: 'Keputusan',
    file: 'sk_koordinator.pdf'
  },
  {
    id: 4,
    nomor: 'EDARAN/005/IV/2026',
    tanggal: '12-04-2026',
    pengirim: 'Biro Administrasi Akademik',
    perihal: 'Edaran Pengisian Kartu Rencana Studi',
    kategori: 'Pemberitahuan',
    file: 'edaran_krs.pdf'
  },
  {
    id: 5,
    nomor: '207/UND/III/2026',
    tanggal: '20-03-2026',
    pengirim: 'Panitia Seminar Nasional',
    perihal: 'Undangan Seminar Teknologi Informasi 2026',
    kategori: 'Undangan',
    file: 'undangan_seminar.pdf'
  }
];

const defaultKategori = [
  { id: 1, nama: 'Undangan', deskripsi: 'Surat untuk menghadiri acara/kegiatan kampus.' },
  { id: 2, nama: 'Pemberitahuan', deskripsi: 'Surat informasi umum atau edaran resmi.' },
  { id: 3, nama: 'Keputusan', deskripsi: 'Dokumen ketetapan atau pengangkatan resmi.' },
  { id: 4, nama: 'Edaran', deskripsi: 'Surat edaran yang ditujukan kepada seluruh civitas.' }
];

const defaultUsers = [
  { id: 1, nama: 'Admin', email: 'admin@polibatam.ac.id', role: 'Admin', status: 'Aktif', lastLogin: '15 Apr 2026, 07:00' },
  { id: 2, nama: 'Karyawan', email: 'karyawan@polibatam.ac.id', role: 'Karyawan', status: 'Aktif', lastLogin: '09 Apr 2026, 10:30' }
];

// Init defaults if not exist
function initStorage() {
  if (!localStorage.getItem(LETTERS_KEY)) {
    localStorage.setItem(LETTERS_KEY, JSON.stringify(defaultLetters));
  }
  if (!localStorage.getItem(KATEGORI_KEY)) {
    localStorage.setItem(KATEGORI_KEY, JSON.stringify(defaultKategori));
  }
  if (!localStorage.getItem(USERS_KEY)) {
    localStorage.setItem(USERS_KEY, JSON.stringify(defaultUsers));
  }
}
initStorage();

// --- Letter CRUD ---
function getLetters() {
  return JSON.parse(localStorage.getItem(LETTERS_KEY)) || [];
}
function getLetterById(id) {
  return getLetters().find(l => l.id === id || l.id === parseInt(id));
}
function addLetter(letter) {
  const letters = getLetters();
  letters.push(letter);
  localStorage.setItem(LETTERS_KEY, JSON.stringify(letters));
}
function updateLetter(id, data) {
  const letters = getLetters().map(l => (l.id === id || l.id === parseInt(id)) ? { ...l, ...data } : l);
  localStorage.setItem(LETTERS_KEY, JSON.stringify(letters));
}
function deleteLetter(id) {
  const letters = getLetters().filter(l => l.id !== id && l.id !== parseInt(id));
  localStorage.setItem(LETTERS_KEY, JSON.stringify(letters));
}

// --- Kategori CRUD ---
function getKategori() {
  return JSON.parse(localStorage.getItem(KATEGORI_KEY)) || [];
}
function getKategoriById(id) {
  return getKategori().find(k => k.id === id || k.id === parseInt(id));
}
function addKategori(k) {
  const list = getKategori();
  list.push(k);
  localStorage.setItem(KATEGORI_KEY, JSON.stringify(list));
}
function updateKategori(id, data) {
  const list = getKategori().map(k => (k.id === id || k.id === parseInt(id)) ? { ...k, ...data } : k);
  localStorage.setItem(KATEGORI_KEY, JSON.stringify(list));
}
function deleteKategori(id) {
  const list = getKategori().filter(k => k.id !== id && k.id !== parseInt(id));
  localStorage.setItem(KATEGORI_KEY, JSON.stringify(list));
}

// --- User CRUD ---
function getUsers() {
  return JSON.parse(localStorage.getItem(USERS_KEY)) || [];
}
function getUserById(id) {
  return getUsers().find(u => u.id === id || u.id === parseInt(id));
}
function addUser(user) {
  const list = getUsers();
  list.push(user);
  localStorage.setItem(USERS_KEY, JSON.stringify(list));
}
function updateUser(id, data) {
  const list = getUsers().map(u => (u.id === id || u.id === parseInt(id)) ? { ...u, ...data } : u);
  localStorage.setItem(USERS_KEY, JSON.stringify(list));
}
function deleteUser(id) {
  const list = getUsers().filter(u => u.id !== id && u.id !== parseInt(id));
  localStorage.setItem(USERS_KEY, JSON.stringify(list));
}
