# Human Robot Interaction Workshop
## Outline
1. Pengantar Robotika & HRI (Konsep Fundamental)
2. Pose Detection
3. Posture Detection
4. HRI : Aplikasi Deteksi Pose/Posture 
5. HRI : Integrasi LLM
6. Pengantar Hands-on Robot Anjing & UR

## Detailed Outline
## Bab 1: Pengantar Robotika & HRI (Harmoni Manusia dan Mesin)
*Bab ini membangun pemahaman dari sudut pandang psikologis dan desain, lalu diakhiri dengan landasan teknis bagaimana robot beroperasi.*

### 1.1 Filosofi dan Psikologi HRI
* Evolusi interaksi: Dari *Teleoperation* (kendali manual jarak jauh) menuju *Autonomous Collaboration* (kolaborasi otonom).
* Fenomena *Uncanny Valley* dan faktor *Trust* (kepercayaan) manusia terhadap mesin.
* Mengurangi *Cognitive Load* (beban kognitif) manusia melalui desain interaksi yang intuitif.

### 1.2 Siklus Inti Robotika (Alur Kerja)
* Paradigma *Sense - Plan - Act* dalam konteks keberadaan manusia di sekitar robot.

### 1.3 Keamanan dan Ergonomi Kolaborasi
* Klasifikasi HRI: *Remote*, *Proximity*, dan *Physical Collaboration*.
* *Safety Zones* (Zona Merah, Kuning, Hijau) dan pengenalan standar keselamatan.

### 1.4 Skenario Aplikatif di Industri & Keseharian
* Robot *pick-and-place* kolaboratif (Cobot), robot asisten medis, dan *social robots*.

> **Referensi / Bahan Bacaan Bab 1:**
> * ISO/TS 15066:2016 (*Robots and robotic devices — Collaborative robots*).
> * *Human-Robot Interaction: An Introduction* (Bartneck et al., 2020).

---

## Bab 2: Pose Detection (Bagaimana Robot "Melihat" Manusia)
*Bab ini membahas bagaimana robot mengubah data visual mentah (piksel/cahaya) menjadi representasi spasial tubuh manusia.*

### 2.1 Konsep Dasar Representasi Visual
* Mengapa robot butuh *skeleton*? (Mereduksi kompleksitas gambar menjadi titik koordinat).
* Konsep *Landmarks/Keypoints* spasial: Beda ruang 2D `(x, y)` dan ruang 3D `(x, y, z)`.

### 2.2 Perangkat Keras vs Algoritma
* Kamera RGB (Standard) vs Kamera *Depth* (RGB-D/LiDAR): Plus-minus dalam mengekstraksi akurasi kedalaman (Z-axis).

### 2.3 Teori Ekstraksi Fitur (Deep Dive Teknis)
* Pendekatan *Top-down* (Deteksi orang dulu, baru pose) vs *Bottom-up* (Deteksi semua sendi, baru gabungkan ke individu).
* Intuisi dasar *Convolutional Neural Networks* (CNN) ringan untuk deteksi tepi/sendi.

### 2.4 Alur Data (Data Pipeline)
* Diagram Alur: `Piksel RGB -> Pre-processing -> Model Inferensi -> Matriks Koordinat (x,y,z)`.
* Tantangan nyata: *Occlusion* (anggota tubuh tertutup objek/orang lain) dan pencahayaan dinamis.

### 2.5 Tools yang Sering Digunakan (Overview)
* MediaPipe (Google), OpenPose, YOLO-Pose.

> **Referensi / Bahan Bacaan Bab 2:**
> * Makalah MediaPipe: *MediaPipe: A Framework for Building Perception Pipelines* (Lugaresi et al., 2019).

---

## Bab 3: Posture Detection (Bagaimana Robot "Memahami" Kondisi Manusia)
*Bab ini memperdalam ekstraksi data—mengubah koordinat spasial (Pose) menjadi pemahaman semantik / kondisi (Posture).*

### 3.1 Perbedaan Fundamental Pose dan Posture
* **Pose:** Angka koordinat absolut (Misal: Lutut di x:100, y:200).
* **Posture:** Makna/Kondisi (Misal: Jongkok, Berdiri, Jatuh).

### 3.2 Rekayasa Fitur (Feature Engineering) Tubuh Manusia
* Menghitung Geometri Sudut (*Joint Angles*): Menggunakan aljabar vektor dasar (*Dot Product*) untuk mencari sudut siku atau lutut.
* Titik Keseimbangan (*Center of Gravity / CoG*): Menentukan apakah manusia dalam keadaan stabil atau kehilangan keseimbangan.

### 3.3 Analisis Spasial vs Temporal
* Transisi Waktu (*Temporal*): Membedakan orang yang "sedang tiduran" dengan "baru saja jatuh" berdasarkan kalkulasi waktu (*Delta Time*).

### 3.4 Pendekatan Klasifikasi
* *Rule-based / Heuristics*: Logika IF-THEN sederhana (misal: `JIKA sudut_lutut < 90 derajat MAKA Postur = Jongkok`).
* *Machine Learning-based*: Menggunakan algoritma seperti *Support Vector Machine* (SVM) atau *Random Forest* untuk postur kompleks berdasarkan dataset.

### 3.5 Diagram Alur Klasifikasi
* `Data Pose (Input) -> Ekstraksi Sudut/Vektor -> Model Klasifikasi -> Label Postur (Output)`.

---

## Bab 4: HRI - Aplikasi Integrasi Pose & Posture
*Bab ini menjembatani hasil deteksi dari Bab 2 & 3 ke dalam sistem kendali robot yang responsif.*

### 4.1 Membaca Niat Manusia (Intent Recognition)
* Menerjemahkan postur menjadi intensi: Apakah manusia butuh bantuan? Apakah manusia memerintahkan robot berhenti?

### 4.2 Arsitektur Sistem Berbasis Node
* Konsep *Publisher-Subscriber* (abstrak dari ROS): Bagaimana Modul Kamera "berteriak" menyiarkan data, dan Modul Roda Robot "mendengarkan" untuk bergerak.

### 4.3 Desain Reaksi & Waktu Respons
* Menghitung *Reaction Time* sistem agar robot tidak menabrak manusia saat terjadi perubahan postur mendadak.

### 4.4 Studi Kasus & Contoh Aplikatif
* **Kasus 1: Gesture-based Control** (Mengendalikan laju dan arah robot AGV hanya dengan lambaian atau penunjukan tangan).
* **Kasus 2: Sistem Pemantauan Keselamatan** (Robot menghentikan operasi mesin berat saat mendeteksi pekerja dalam postur kelelahan atau terjatuh di zona merah).

---

## Bab 5: HRI - Integrasi LLM pada Robotika (Kognisi Tingkat Tinggi)
*Bab ini membahas paradigma terbaru: memberikan "otak" bahasa natural pada robot agar tidak kaku pada aturan pemrograman tradisional (FSM).*

### 5.1 Evolusi Kendali Robot: FSM menuju LLM
* Batasan *Finite State Machine* (FSM) yang kaku (robot bingung jika ada perintah di luar skrip).
* Paradigma *Zero-shot robot control*: Robot mampu memahami dan mengeksekusi perintah yang belum pernah diprogram sebelumnya.

### 5.2 LLM sebagai Penterjemah Aksi (Task Decomposition)
* Bagaimana LLM memecah perintah abstrak ("Ambilkan saya minum") menjadi aksi diskrit (`Temukan gelas -> Bergerak ke dapur -> Ambil gelas -> Kembali ke manusia`).

### 5.3 Menggabungkan Visi dan Teks (VLM - Vision-Language Models)
* Arsitektur VLM: Menggabungkan teks *prompt* dari LLM dengan input gambar dari Modul Kamera/Pose.

### 5.4 Skenario Utuh (Menggabungkan Bab 1 - Bab 5)
* **Simulasi Pipeline:** Manusia terjatuh (Pose terekam -> Postur diklasifikasikan sebagai 'Jatuh') -> Modul VLM melihat gambar dan konteks "Manusia jatuh di dekat tangga" -> LLM menganalisis tingkat bahaya -> LLM menginstruksikan robot (via teks-ke-fungsi) untuk membunyikan alarm medis dan mendekat untuk memberikan P3K.

> **Referensi / Bahan Bacaan Bab 5:**
> * *Do As I Can, Not As I Say: Grounding Language in Robotic Affordances* (Ahn et al., 2022 - SayCan by Google).
> * *RT-1: Robotics Transformer for Real-World Control at Scale* (Brohan et al., 2022).