-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 20, 2026 at 06:25 AM
-- Server version: 8.0.30
-- PHP Version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `arsip_surat`
--

-- --------------------------------------------------------

--
-- Table structure for table `aktivitas_log`
--

CREATE TABLE `aktivitas_log` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `kegiatan` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `waktu` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `aktivitas_log`
--

INSERT INTO `aktivitas_log` (`id`, `user_id`, `kegiatan`, `status`, `waktu`) VALUES
(1, 1, 'Login ke sistem', 'Sukses', '2026-07-06 09:56:46'),
(2, 1, 'Login ke sistem', 'Sukses', '2026-07-08 11:52:19'),
(3, 1, 'Login ke sistem', 'Sukses', '2026-07-10 15:47:08'),
(4, 1, 'Menambahkan surat: 700/PL29/HM.00.02/2026', 'Selesai', '2026-07-10 20:52:49'),
(5, 1, 'Menambahkan surat: 1 1261/PL29/HM.00.03/2026', 'Selesai', '2026-07-10 20:53:11'),
(6, 1, 'Menambahkan surat: 797/PL29/HM.00.00/2026', 'Selesai', '2026-07-10 20:53:16'),
(7, 1, 'Menambahkan surat: 728/PL29/HM.00.00/2026', 'Selesai', '2026-07-10 20:53:22'),
(8, 1, 'Logout dari sistem', 'Sukses', '2026-07-10 20:55:59'),
(9, 1, 'Login ke sistem', 'Sukses', '2026-07-10 21:10:54'),
(10, 1, 'Logout dari sistem', 'Sukses', '2026-07-10 21:33:27'),
(11, 2, 'Login ke sistem', 'Sukses', '2026-07-10 21:33:34'),
(12, 2, 'Memperbarui profil', 'Sukses', '2026-07-10 21:33:51'),
(13, 1, 'Login ke sistem', 'Sukses', '2026-07-11 13:07:58'),
(14, 1, 'Login ke sistem', 'Sukses', '2026-07-11 20:25:01'),
(15, 1, 'Logout dari sistem', 'Sukses', '2026-07-11 20:26:11'),
(16, 1, 'Login ke sistem', 'Sukses', '2026-07-11 20:44:49'),
(17, 1, 'Logout dari sistem', 'Sukses', '2026-07-11 21:03:58'),
(18, 2, 'Login ke sistem', 'Sukses', '2026-07-11 21:04:15'),
(19, 2, 'Logout dari sistem', 'Sukses', '2026-07-11 21:16:34'),
(20, 1, 'Login ke sistem', 'Sukses', '2026-07-11 23:36:48'),
(21, 1, 'Logout dari sistem', 'Sukses', '2026-07-11 23:40:53'),
(22, 2, 'Login ke sistem', 'Sukses', '2026-07-11 23:41:22'),
(23, 2, 'Logout dari sistem', 'Sukses', '2026-07-11 23:47:28'),
(24, 1, 'Login ke sistem', 'Sukses', '2026-07-11 23:51:34'),
(25, 1, 'Login ke sistem', 'Sukses', '2026-07-12 16:07:40'),
(26, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 16:10:12'),
(27, 2, 'Login ke sistem', 'Sukses', '2026-07-12 16:10:24'),
(28, 2, 'Logout dari sistem', 'Sukses', '2026-07-12 16:10:53'),
(29, 1, 'Login ke sistem', 'Sukses', '2026-07-12 16:11:34'),
(30, 1, 'Mengubah surat: 728/PL29/HM.00.00/2026', 'Selesai', '2026-07-12 16:11:57'),
(31, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 16:13:08'),
(32, 2, 'Login ke sistem', 'Sukses', '2026-07-12 16:13:11'),
(33, 2, 'Logout dari sistem', 'Sukses', '2026-07-12 16:24:54'),
(34, 1, 'Login ke sistem', 'Sukses', '2026-07-12 16:24:57'),
(35, 1, 'Mengubah surat: 728/PL29/HM.00.00/2026', 'Selesai', '2026-07-12 16:27:56'),
(36, 1, 'Mengubah surat: 797/PL29/HM.00.00/2026', 'Selesai', '2026-07-12 16:28:00'),
(37, 1, 'Mengubah surat: 1 1261/PL29/HM.00.03/2026', 'Selesai', '2026-07-12 16:28:02'),
(38, 1, 'Mengubah surat: 700/PL29/HM.00.02/2026', 'Selesai', '2026-07-12 16:28:05'),
(39, 1, 'Mengubah kategori: Surat Undangan', 'Selesai', '2026-07-12 16:38:25'),
(40, 1, 'Mengubah kategori: Surat Pemberitahuan', 'Selesai', '2026-07-12 16:38:35'),
(41, 1, 'Mengubah kategori: Surat Keputusan', 'Selesai', '2026-07-12 16:38:39'),
(42, 1, 'Mengubah kategori: Surat Undangan', 'Selesai', '2026-07-12 16:39:36'),
(43, 1, 'Mengubah kategori: Surat Pemberitahuan', 'Selesai', '2026-07-12 16:39:55'),
(44, 1, 'Mengubah kategori: Surat Keputusan', 'Selesai', '2026-07-12 16:40:03'),
(45, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 17:03:05'),
(46, 1, 'Login ke sistem', 'Sukses', '2026-07-12 17:59:14'),
(47, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 18:00:52'),
(48, 2, 'Login ke sistem', 'Sukses', '2026-07-12 18:00:59'),
(49, 2, 'Logout dari sistem', 'Sukses', '2026-07-12 20:36:27'),
(50, 1, 'Login ke sistem', 'Sukses', '2026-07-12 20:37:14'),
(51, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 20:37:44'),
(52, 1, 'Login ke sistem', 'Sukses', '2026-07-12 20:38:57'),
(53, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 20:39:46'),
(54, 1, 'Login ke sistem', 'Sukses', '2026-07-12 20:40:54'),
(55, 1, 'Logout dari sistem', 'Sukses', '2026-07-12 20:44:16'),
(56, 2, 'Login ke sistem', 'Sukses', '2026-07-12 20:44:28'),
(57, 1, 'Login ke sistem', 'Sukses', '2026-07-14 23:42:35'),
(58, 1, 'Logout dari sistem', 'Sukses', '2026-07-14 23:42:52'),
(59, 1, 'Login ke sistem', 'Sukses', '2026-07-21 19:19:02'),
(60, 1, 'Login ke sistem', 'Sukses', '2026-07-21 19:35:31'),
(61, 1, 'Logout dari sistem', 'Sukses', '2026-07-21 21:04:35'),
(62, 1, 'Login ke sistem', 'Sukses', '2026-07-21 21:05:33'),
(63, 1, 'Logout dari sistem', 'Sukses', '2026-07-21 21:05:48'),
(64, 1, 'Logout dari sistem', 'Sukses', '2026-07-21 21:13:34'),
(65, 1, 'Login ke sistem', 'Sukses', '2026-07-21 21:14:01'),
(66, 2, 'Login ke sistem', 'Sukses', '2026-07-21 21:16:48'),
(67, 1, 'Login ke sistem', 'Sukses', '2026-07-22 14:09:28'),
(68, 1, 'Login ke sistem', 'Sukses', '2026-07-22 14:13:42'),
(69, 2, 'Login ke sistem', 'Sukses', '2026-07-22 14:19:50'),
(70, 1, 'Login ke sistem', 'Sukses', '2026-07-23 10:57:17');

-- --------------------------------------------------------

--
-- Table structure for table `kategori`
--

CREATE TABLE `kategori` (
  `id` int NOT NULL,
  `nama` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `deskripsi` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `kategori`
--

INSERT INTO `kategori` (`id`, `nama`, `deskripsi`) VALUES
(1, 'Surat Undangan', 'Surat undangan adalah surat resmi yang dibuat untuk mengundang seseorang atau suatu pihak agar menghadiri kegiatan, acara, rapat, atau pertemuan pada waktu dan tempat yang telah ditentukan.'),
(2, 'Surat Pemberitahuan', 'Surat pemberitahuan adalah surat resmi yang digunakan untuk menyampaikan informasi, pengumuman, atau perubahan tertentu kepada pihak yang dituju agar mengetahui dan memahami informasi tersebut.'),
(3, 'Surat Keputusan', 'Surat keputusan adalah surat resmi yang berisi penetapan atau keputusan yang dibuat oleh pejabat atau pihak yang berwenang mengenai suatu hal, seperti pengangkatan, pemberhentian, penetapan kebijakan, atau keputusan administratif lainnya. Surat ini bersifat mengikat bagi pihak yang terkait.');

-- --------------------------------------------------------

--
-- Table structure for table `surat`
--

CREATE TABLE `surat` (
  `id` int NOT NULL,
  `nomor_surat` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tanggal_surat` date NOT NULL,
  `pengirim` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `perihal` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `kategori_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `surat`
--

INSERT INTO `surat` (`id`, `nomor_surat`, `tanggal_surat`, `pengirim`, `perihal`, `file_path`, `kategori_id`, `created_at`) VALUES
(1, '700/PL29/HM.00.02/2026', '2026-04-13', 'KEMENTERIAN PENDIDIKAN TINGGI', 'Undangan FGD Penerapan Smart Street Lighting', 'static/uploads/700_Undangan_Wali_Kota_-_FGD_Penerapan_Smart_Street_Lighting_sebagai_Backbone_Smart_City_di_Kota_Batam_2.pdf', 1, '2026-07-10 20:52:49'),
(2, '1 1261/PL29/HM.00.03/2026', '2026-06-09', 'KEMENTERIAN PENDIDIKAN TINGGI', 'Undangan Rapat Koordinasi Pembentukan Konsorsium', 'static/uploads/1261_Undangan_Rakor_Pembentukan_Konsorsioum_PPKPT_se-Kota_Batam.pdf', 1, '2026-07-10 20:53:11'),
(3, '797/PL29/HM.00.00/2026', '2026-04-21', 'KEMENTERIAN PENDIDIKAN TINGGI', 'Undangan Penandatanganan Perjanjian Kerja Sama', 'static/uploads/797_Undangan_Penandatanganan_Perjanjian_Kerja_Sama.pdf', 1, '2026-07-10 20:53:16'),
(4, '728/PL29/HM.00.00/2026', '2026-04-14', 'KEMENTERIAN PENDIDIKAN TINGGI', 'Undangan kegiatan Doa Bersama', 'static/uploads/728_Undangan_kegiatan_Doa_Bersama_-_Rektor_UMRAH.pdf', 1, '2026-07-10 20:53:22');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `nama` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `foto` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `nama`, `email`, `password`, `role`, `foto`) VALUES
(1, 'Administrator', 'admin@polibatam.ac.id', 'scrypt:32768:8:1$rwGlI44dmFAWUKUW$364cef92af3926e189b3f766d27183a2abcdf78fe47b3e7aabc740632048a290b986b4ff37e4fd86d02968c559a7aba04f6a19d8411f3e77f4bc73e8a4171649', 'Admin', NULL),
(2, 'Karyawan', 'karyawan@polibatam.ac.id', 'scrypt:32768:8:1$6mDVZHBJMp13qPXk$5ff89f1a7b6a54c751bcab6164046232be6a669db75b01de727e2de45bfc820fdc2ebf69dea86d96744f0531e7b4c7a0b335ea98540a7f151405b40bd9b5e825', 'Karyawan', NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `aktivitas_log`
--
ALTER TABLE `aktivitas_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `kategori`
--
ALTER TABLE `kategori`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `surat`
--
ALTER TABLE `surat`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nomor_surat` (`nomor_surat`),
  ADD KEY `kategori_id` (`kategori_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `aktivitas_log`
--
ALTER TABLE `aktivitas_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=71;

--
-- AUTO_INCREMENT for table `kategori`
--
ALTER TABLE `kategori`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `surat`
--
ALTER TABLE `surat`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `aktivitas_log`
--
ALTER TABLE `aktivitas_log`
  ADD CONSTRAINT `aktivitas_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `surat`
--
ALTER TABLE `surat`
  ADD CONSTRAINT `surat_ibfk_1` FOREIGN KEY (`kategori_id`) REFERENCES `kategori` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
