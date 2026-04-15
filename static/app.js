/* ============================================================
   DigiSurat - App Logic (shared across all pages)
   ============================================================ */

/* ---- Toast ---- */
function showToast(msg, type = 'info') {
  const c = document.getElementById('toastContainer');
  if (!c) return;
  const t = document.createElement('div');
  const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle';
  t.className = `toast ${type}`;
  t.innerHTML = `<i class="fa-solid fa-${icon}"></i> ${msg}`;
  c.appendChild(t);
  setTimeout(() => {
    t.classList.add('fade-out');
    setTimeout(() => t.remove(), 350);
  }, 3200);
}

/* ---- Dropdown User Menu ---- */
function toggleDropdown() {
  const menu = document.getElementById('dropdownMenu');
  if (menu) menu.classList.toggle('open');
}

document.addEventListener('click', (e) => {
  const btn = document.getElementById('userMenuBtn');
  const menu = document.getElementById('dropdownMenu');
  if (menu && btn && !btn.contains(e.target) && !menu.contains(e.target)) {
    menu.classList.remove('open');
  }
});

/* ---- Modal ---- */
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

/* ---- Ganti Sandi ---- */
function openGantiSandi() {
  const menu = document.getElementById('dropdownMenu');
  if (menu) menu.classList.remove('open');
  openModal('gantiSandiModal');
}

function submitGantiSandi() {
  const oldPass = document.getElementById('oldPass').value;
  const newPass = document.getElementById('newPass').value;
  const confirmPass = document.getElementById('confirmPass').value;

  if (!oldPass || !newPass || !confirmPass) {
    showToast('Harap isi semua field password!', 'error'); return;
  }
  if (newPass.length < 6) {
    showToast('Password baru minimal 6 karakter!', 'error'); return;
  }
  if (newPass !== confirmPass) {
    showToast('Konfirmasi password tidak cocok!', 'error'); return;
  }
  closeModal('gantiSandiModal');
  showToast('Password berhasil diubah!', 'success');
  document.getElementById('oldPass').value = '';
  document.getElementById('newPass').value = '';
  document.getElementById('confirmPass').value = '';
  const bar = document.getElementById('passStrengthBar');
  const lbl = document.getElementById('passStrengthLabel');
  if (bar) { bar.className = 'password-strength'; }
  if (lbl) { lbl.textContent = ''; }
}

function checkStrength(val) {
  const bar = document.getElementById('passStrengthBar');
  const lbl = document.getElementById('passStrengthLabel');
  if (!bar) return;
  if (val.length === 0) {
    bar.className = 'password-strength';
    if (lbl) lbl.textContent = '';
    return;
  }
  if (val.length < 6) {
    bar.className = 'password-strength strength-weak';
    if (lbl) { lbl.textContent = 'Lemah'; lbl.style.color = '#ef4444'; }
  } else if (val.length < 10 || !/[0-9]/.test(val) || !/[A-Z]/.test(val)) {
    bar.className = 'password-strength strength-medium';
    if (lbl) { lbl.textContent = 'Sedang'; lbl.style.color = '#f59e0b'; }
  } else {
    bar.className = 'password-strength strength-strong';
    if (lbl) { lbl.textContent = 'Kuat'; lbl.style.color = '#22c55e'; }
  }
}

/* ---- Toggle Password Eye ---- */
function togglePassField(fieldId, btn) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  const icon = btn.querySelector('i');
  if (field.type === 'password') {
    field.type = 'text';
    if (icon) { icon.className = 'fa-solid fa-eye-slash'; }
  } else {
    field.type = 'password';
    if (icon) { icon.className = 'fa-solid fa-eye'; }
  }
}

/* ---- Logout ---- */
function handleLogout() {
  const menu = document.getElementById('dropdownMenu');
  if (menu) menu.classList.remove('open');
  openModal('logoutModal');
}

function confirmLogout() {
  closeModal('logoutModal');
  showToast('Berhasil logout. Mengarahkan ke halaman login...', 'info');
  setTimeout(() => { window.location.href = 'login.html'; }, 1200);
}

/* ---- Render Tables ---- */

// Karyawan table (read-only with download) - sesuai gambar referensi
function renderKaryawanTable(tbodyId, limit) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  const letters = getLetters().slice(0, limit === Infinity ? undefined : limit);
  if (letters.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-muted);"><i class="fa-solid fa-inbox" style="font-size:1.5rem;display:block;margin-bottom:8px;"></i>Belum ada data surat</td></tr>`;
    return;
  }
  tbody.innerHTML = letters.map((l, i) => `
    <tr>
      <td>${i + 1}</td>
      <td style="font-size:0.83rem;">${l.nomor}</td>
      <td>${l.tanggal}</td>
      <td style="font-size:0.83rem;">${l.pengirim}</td>
      <td style="font-size:0.83rem;">${l.perihal}</td>
      <td style="font-size:0.83rem;">${l.kategori}</td>
      <td style="font-size:0.83rem;">${l.file}</td>
      <td>
        <button style="background:none;border:none;cursor:pointer;display:inline-flex;align-items:center;gap:5px;font-size:0.83rem;font-weight:500;color:var(--text-primary);padding:4px 2px;transition:color 0.2s;" title="Unduh" onclick="downloadSurat(${l.id})" onmouseover="this.style.color='var(--accent)'" onmouseout="this.style.color='var(--text-primary)'">
          <i class="fa-solid fa-download" style="font-size:0.8rem;"></i> Unduh
        </button>
      </td>
    </tr>
  `).join('');
}

// Admin surat table (with edit & delete)
function renderAdminSuratTable(tbodyId, limit) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  const letters = getLetters().slice(0, limit === Infinity ? undefined : limit);
  if (letters.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-muted);"><i class="fa-solid fa-inbox" style="font-size:1.5rem;display:block;margin-bottom:8px;"></i>Belum ada data surat</td></tr>`;
    return;
  }
  tbody.innerHTML = letters.map((l, i) => `
    <tr>
      <td>${i + 1}</td>
      <td style="font-size:0.83rem;">${l.nomor}</td>
      <td>${l.tanggal}</td>
      <td style="font-size:0.83rem;">${l.pengirim}</td>
      <td style="font-size:0.83rem;">${l.perihal}</td>
      <td><span class="badge-info">${l.kategori}</span></td>
      <td style="font-size:0.83rem;color:var(--accent);"><i class="fa-regular fa-file-pdf"></i> ${l.file}</td>
      <td style="white-space:nowrap;">
        <button class="action-btn btn-edit" title="Edit" onclick="openEditSurat(${l.id})">
          <i class="fa-solid fa-pen-to-square"></i>
        </button>
        <button class="action-btn btn-delete" title="Hapus" onclick="openDeleteSurat(${l.id})" style="margin-left:4px;">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

// Dashboard admin table (no action column)
function renderDashboardTable(tbodyId, showAction) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  const letters = getLetters().slice(0, 5);
  if (letters.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--text-muted);">Belum ada data surat</td></tr>`;
    return;
  }
  tbody.innerHTML = letters.map((l, i) => `
    <tr>
      <td>${i + 1}</td>
      <td style="font-size:0.83rem;">${l.nomor}</td>
      <td>${l.tanggal}</td>
      <td style="font-size:0.83rem;">${l.pengirim}</td>
      <td style="font-size:0.83rem;">${l.perihal}</td>
      <td><span class="badge-info">${l.kategori}</span></td>
      <td style="font-size:0.83rem;color:var(--accent);"><i class="fa-regular fa-file-pdf"></i> ${l.file}</td>
    </tr>
  `).join('');
}

// Kategori table
function renderKategoriTable() {
  const tbody = document.getElementById('kategoriTableBody');
  if (!tbody) return;
  const list = getKategori();
  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:32px;color:var(--text-muted);">Belum ada kategori</td></tr>`;
    return;
  }
  tbody.innerHTML = list.map((k, i) => `
    <tr>
      <td>${i + 1}</td>
      <td style="font-weight:600;">${k.nama}</td>
      <td style="font-size:0.85rem;color:var(--text-secondary);">${k.deskripsi || '–'}</td>
      <td style="white-space:nowrap;">
        <button class="action-btn btn-edit" title="Edit" onclick="openEditKategori(${k.id})">
          <i class="fa-solid fa-pen-to-square"></i>
        </button>
        <button class="action-btn btn-delete" title="Hapus" onclick="openDeleteKategori(${k.id})" style="margin-left:4px;">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

// User table
function renderUserTable() {
  const tbody = document.getElementById('userTableBody');
  if (!tbody) return;
  const users = getUsers();
  if (users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--text-muted);">Belum ada data user</td></tr>`;
    return;
  }
  tbody.innerHTML = users.map((u, i) => `
    <tr>
      <td>${i + 1}</td>
      <td style="font-weight:600;">${u.nama}</td>
      <td style="font-size:0.83rem;">${u.email}</td>
      <td><span class="user-role-badge ${u.role === 'Admin' ? 'role-admin' : 'role-karyawan'}">${u.role}</span></td>
      <td><span class="${u.status === 'Aktif' ? 'status-active' : 'status-inactive'}">${u.status}</span></td>
      <td style="font-size:0.83rem;color:var(--text-secondary);">${u.lastLogin || '-'}</td>
      <td style="white-space:nowrap;">
        <button class="action-btn btn-edit" title="Edit" onclick="openEditUser(${u.id})">
          <i class="fa-solid fa-pen-to-square"></i>
        </button>
        <button class="action-btn btn-delete" title="Hapus" onclick="openDeleteUser(${u.id})" style="margin-left:4px;">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

/* ---- Download Surat ---- */
function downloadSurat(id) {
  const l = getLetterById(id);
  if (l) {
    showToast(`Mengunduh ${l.file}...`, 'success');
  }
}

/* ---- Init Page ---- */
function initPage(pageName) {
  // Escape key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
      const menu = document.getElementById('dropdownMenu');
      if (menu) menu.classList.remove('open');
    }
  });
}
