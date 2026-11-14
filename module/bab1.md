# Bab 1: Pengantar Robotika & Human-Robot Interaction

Bayangkan sebuah robot yang selama ini kita lihat bekerja di balik pagar kaca pabrik atau dikendalikan lewat *remote control* yang rumit, kini keluar dari "kandangnya" dan berdiri tepat di sebelahmu. Ia bisa mengerti saat kamu melambaikan tangan, berhenti otomatis saat kamu melangkah terlalu dekat, bahkan memahami perintah bahasa sehari-hari seperti manusia.

Perubahan cara kerja inilah yang menjadi inti dari **Human-Robot Interaction (HRI)**. Sebelum kita langsung menyentuh kamera, melatih model deteksi pose, dan menghubungkannya ke **Robot UR** maupun **RoboDog** pada sesi praktikum, penting bagi kita untuk memahami fondasi di balik layar: bagaimana robot sebenarnya bekerja, bagaimana manusia memandang kehadiran mesin di ruang fisik yang sama, serta aturan keselamatan apa yang membuat kolaborasi keduanya berjalan aman dan nyaman.

**Setelah mempelajari Bab 1 ini, kamu diharapkan mampu:**

* Memahami anatomi dasar sistem robotik dan pergeseran paradigma dari robotika tradisional menuju HRI.
* Menjelaskan siklus kerja inti robotika (**Sense – Plan – Act**) serta tantangan latensi saat berinteraksi dengan manusia secara *real-time*.
* Mengenali faktor psikologis manusia terhadap robot (*Uncanny Valley*, *trust*, dan beban kognitif) serta arsitektur zona keselamatan (*Safety Zones* dan standar ISO/TS 15066).
* Mengidentifikasi penerapan nyata HRI di berbagai sektor industri, riset akademis, hingga kehidupan sehari-hari.

## 1.1 Dari Robotika Menuju Human-Robot Interaction (HRI)

### 1.1.1 Mengenal Robot dan Robotika

Secara sederhana, **robot** adalah mesin fisik yang dapat diprogram untuk merasakan lingkungan sekitarnya, memproses informasi tersebut, lalu melakukan tindakan nyata di dunia fisik. Sementara itu, **robotika** adalah bidang ilmu yang merancang, membangun, dan mengendalikan mesin tersebut.

Agar bisa bekerja, sebuah sistem robotik umumnya memiliki tiga komponen utama yang mirip dengan tubuh manusia:

* **Sensors (Indra):** Alat untuk menangkap data dari lingkungan, seperti kamera (mata), LiDAR (pengukur jarak), dan *encoder* (sensor posisi sudut pada sendi).
* **Controller / Compute (Otak):** Komputer mini atau mikrokontroler yang mengolah data sensor dan mengambil keputusan.
* **Actuators (Otot):** Komponen penggerak seperti motor servo atau sistem hidrolik yang membuat robot bisa bergerak.

Dalam workshop ini, kita akan berhadapan dengan dua jenis bentuk robot yang sangat populer:

1. **Manipulator / Articulated Robot (Contoh: Robot UR):** Lengan robot statis dengan beberapa sendi (*Degrees of Freedom*) yang dirancang untuk presisi tinggi, seperti mengambil dan memindahkan barang.
2. **Mobile & Legged Robot (Contoh: RoboDog):** Robot bergerak yang menggunakan kaki (desain menyerupai hewan/zoomorfik) sehingga mampu melintasi medan yang tidak rata seperti tangga atau jalan berbatu.

> **[PLACEHOLDER GAMBAR 1.1: Anatomi Dasar Sistem Robotik & Jenis Robot]**
> *Deskripsi Ilustrasi: Diagram blok sederhana yang menghubungkan `Sensors -> Controller -> Actuators`, berdampingan dengan foto/vektor perbandingan antara Lengan Robot UR (statis, multi-sendi) dan RoboDog (berkaki empat, bergerak bebas).*

---

### 1.1.2 Lahirnya HRI: Ketika Robot Keluar dari "Kandang"

Pada awal era industri, robot bekerja di dalam pagar pengaman (*safety cage*) yang terisolasi dari manusia. Alasannya sederhana: robot zaman dulu bergerak cepat, bertenaga besar, namun "buta" terhadap keberadaan manusia di sekitarnya. Jika ada pekerja masuk ke area robot saat mesin menyala, risikonya fatal.

Namun, paradigma ini berubah total. Muncul kebutuhan agar manusia dan robot bisa bekerja berdampingan dalam satu ruang kerja yang sama (*shared workspace*). Manusia unggul dalam fleksibilitas dan pengambilan keputusan kompleks, sementara robot unggul dalam presisi, kekuatan, dan pekerjaan berulang. Dari sinilah lahir bidang **Human-Robot Interaction (HRI)**—ilmu yang mempelajari bagaimana merancang sistem agar manusia dan robot dapat berkomunikasi dan berkolaborasi secara aman serta efektif.

**Apa bedanya HRI dengan HCI (*Human-Computer Interaction*)?**
HCI berfokus pada interaksi manusia dengan layar (aplikasi, *website*, atau *smartphone*). Sebaliknya, HRI berurusan dengan **Embodied AI**—kecerdasan yang memiliki wujud fisik, massa, dan bergerak di ruang nyata. Dalam HCI, kesalahan sistem hanya memunculkan pesan *error* di layar; dalam HRI, kesalahan sistem bisa berujung pada benturan fisik.

> **[PLACEHOLDER GAMBAR 1.2: Evolusi Ruang Kerja Robot]**
> *Deskripsi Ilustrasi: Perbandingan dua panel. Panel kiri menunjukkan robot industri klasik di dalam pagar pembatas (terisolasi). Panel kanan menunjukkan manusia dan robot kolaboratif (Cobot) bekerja berdampingan di satu meja tanpa pagar pembatas.*

---

### 1.1.3 Spektrum Otonomi dalam Interaksi

Hubungan kerja antara manusia dan robot tidak selalu sama; ada spektrum pembagian kendali yang bergantung pada seberapa pintar robot tersebut:

1. **Teleoperation (Kendali Penuh):** Robot tidak punya inisiatif sendiri. Manusia mengendalikan setiap gerakan sendi atau arah jalan robot secara manual menggunakan *joystick* atau *teach pendant*.
2. **Supervisory Control (Kendali Pengawasan):** Manusia hanya memberikan target akhir (misalnya: *"Pindahkan kotak dari titik A ke titik B"*), lalu robot menghitung rute dan gerakannya sendiri sementara manusia mengawasi.
3. **Autonomous Collaboration (Kolaborasi Otonom):** Level tertinggi di mana robot mampu mengamati lingkungan, membaca niat manusia (lewat bahasa tubuh atau perintah suara), dan menyesuaikan aksinya secara mandiri secara *real-time*.

---

### 1.1.4 Psikologi Interaksi: Persepsi, *Uncanny Valley*, dan *Trust*

Karena robot hadir secara fisik, otak manusia secara otomatis meresponsnya secara psikologis:

* **Antropomorfisme & Zoomorfisme:** Manusia punya kecenderungan alami memperlakukan benda bergerak seolah memiliki nyawa atau perasaan. Saat berinteraksi dengan **Robot UR**, kita melihatnya murni sebagai alat mekanis. Namun saat berinteraksi dengan **RoboDog**, bentuknya yang menyerupai anjing memicu *zoomorfisme*—kita cenderung merasa lebih akrab, bahkan bersimpati saat robot tersebut "terjatuh".
* **Fenomena *Uncanny Valley*:** Diperkenalkan oleh Masahiro Mori (1970), teori ini menjelaskan bahwa semakin mirip robot dengan manusia, tingkat kenyamanan kita akan meningkat—**tetapi hanya sampai titik tertentu**. Jika robot terlihat *hampir* persis seperti manusia namun gerakannya masih kaku atau tatapannya kosong, manusia justru akan merasa ngeri dan tidak nyaman. Inilah alasan mengapa Robot UR dan RoboDog sengaja didesain fungsional dan tidak diberi wajah manusia.
* **Kalibrasi Kepercayaan (*Trust*):** Kolaborasi akan gagal jika manusia terlalu takut pada robot (*under-trust*) sehingga enggan mendekat, atau sebaliknya, terlalu percaya (*over-trust*) sehingga mengabaikan aspek keselamatan. Kunci membangun *trust* yang sehat adalah **keterbacaan gerak (*legible motion*)** dan **umpan balik (*feedback*)** yang jelas—misalnya lampu indikator berubah warna atau robot mengangguk saat perintah berhasil dipahami.

> **[PLACEHOLDER GAMBAR 1.3: Grafik Kurva Uncanny Valley]**
> *Deskripsi Ilustrasi: Grafik sumbu X (Kemiripan dengan Manusia) dan sumbu Y (Tingkat Kenyamanan/Affinity). Tandai posisi **Robot UR** di area kiri (mekanis/netral), **RoboDog** di area menanjak (zoomorfik/lucu), dan area lembah curam (*Uncanny Valley*) di bagian kanan sebelum mencapai manusia asli.*

---

### 1.1.5 Menurunkan Beban Kognitif (*Cognitive Load*)

Tantangan terbesar dalam HRI adalah menerjemahkan keinginan manusia menjadi bahasa mesin. Jika operator harus menghafal puluhan kombinasi tombol *joystick* atau menulis baris kode koordinat setiap kali ingin menggerakkan robot, otak manusia akan cepat lelah (**beban kognitif tinggi**).

Solusinya adalah menghadirkan **Natural User Interface (NUI)**—membuat robot beradaptasi dengan cara komunikasi alami manusia sehari-hari:

* **Komunikasi Non-Verbal:** Menggunakan gestur tangan dan postur tubuh (yang akan kita bangun menggunakan **Pose Detection** di *Hands-on* 1–3).
* **Komunikasi Verbal:** Menggunakan instruksi bahasa manusia sehari-hari yang fleksibel (yang akan kita bangun menggunakan **LLM** di *Hands-on* 4).

Dengan memindahkan beban "penerjemahan" ini dari otak manusia ke kecerdasan buatan (AI), berinteraksi dengan robot menjadi semudah memberi isyarat atau berbicara kepada rekan kerja.

> **[PLACEHOLDER GAMBAR 1.4: Perbandingan Alur Beban Kognitif]**
> *Deskripsi Ilustrasi: Dua jalur alur interaksi. Jalur atas (Beban Tinggi): `Manusia -> Belajar Bahasa Mesin (Kode/Joystick Rumit) -> Robot`. Jalur bawah (Beban Rendah / NUI): `Manusia -> Gestur Tubuh / Bahasa Alami -> AI (Pose & LLM) -> Robot`.*

## 1.2 Siklus Inti Robotika (*Sense - Plan - Act*)

### 1.2.1 Paradigma *Sense - Plan - Act* (SPA): Jantung Operasi Robot

Pada subbab sebelumnya, kita sudah mengenal tiga komponen fisik utama robot: *Sensors*, *Controller*, dan *Actuators*. Agar robot bisa "hidup" dan berinteraksi, ketiga komponen tersebut dihubungkan dalam satu siklus kerja yang berputar terus-menerus, dikenal sebagai paradigma **Sense – Plan – Act (SPA)**:

1. **Sense (Merasakan):** Robot mengumpulkan data mentah dari lingkungan dan kondisi dirinya sendiri melalui sensor.
2. **Plan (Merencanakan):** "Otak" robot mengolah data sensor tersebut untuk memahami situasi dan memutuskan langkah apa yang harus diambil.
3. **Act (Bertindak):** Robot mengeksekusi keputusan tersebut menjadi gerakan fisik melalui aktuator.

Dalam HRI, siklus ini wajib berjalan sebagai **Closed-Loop System (Sistem Lingkar Tertutup)**. Artinya, proses tidak berhenti setelah robot bergerak (*Act*). Robot harus terus membaca **Feedback (umpan balik)** melalui sensornya untuk memastikan apakah gerakannya sudah sesuai target dan apakah posisi manusia di sekitarnya telah berubah. Sebaliknya, sistem *Open-Loop* bergerak secara "buta" tanpa mengecek hasil aksinya—sesuatu yang sangat berbahaya jika diterapkan di dekat manusia.

> **[PLACEHOLDER GAMBAR 1.5: Diagram Siklus Closed-Loop Sense - Plan - Act]**
> *Deskripsi Ilustrasi: Diagram panah melingkar yang menghubungkan `Sense (Sensors) -> Plan (Controller/AI) -> Act (Actuators)` ke `Lingkungan & Manusia`, disertai panah balik berlabel `Feedback / Perubahan Lingkungan` yang masuk kembali ke tahap `Sense`.*

---

### 1.2.2 Bedah Tiap Tahap dalam Konteks HRI

Ketika robot berinteraksi langsung dengan manusia, setiap tahap dalam siklus SPA memiliki peran spesifik:

* **Tahap 1: *Sense* (Persepsi Lingkungan & Kondisi Internal)**
Robot membutuhkan dua jenis pengindraan sekaligus:
* *Exteroceptive Sensing (Mengamati dunia luar):* Mengumpulkan informasi di sekitar robot, seperti kamera yang menangkap posisi dan gestur tubuh manusia, atau sensor jarak untuk mendeteksi rintangan.


* *Proprioceptive Sensing (Mengamati kondisi internal):* Memantau kondisi tubuh robot itu sendiri—misalnya sensor pada sendi **Robot UR** untuk mengetahui sudut lengannya saat ini, atau sensor keseimbangan (IMU) pada **RoboDog** agar tidak terjatuh saat melangkah.




* **Tahap 2: *Plan* (Pemrosesan, Kognisi & Pengambilan Keputusan)**
Data mentah dari kamera hanyalah kumpulan piksel angka yang belum bermakna. Pada tahap *Plan*, terjadi dua proses penting:
* *Persepsi Tingkat Tinggi:* Mengubah piksel gambar menjadi informasi yang bisa dipahami, misalnya mendeteksi titik-titik sendi manusia lalu mengklasifikasikannya sebagai gestur "angkat tangan".


* *Pengambilan Keputusan:* Menentukan respons yang tepat. Keputusan ini bisa berbasis aturan sederhana (*Rule-based*, seperti: *"Jika tangan kanan diangkat, maka robot menyapa"*), maupun berbasis penalaran kecerdasan buatan seperti **LLM** untuk menerjemahkan perintah bahasa yang lebih kompleks.




* **Tahap 3: *Act* (Eksekusi Fisik & Komunikasi Balik)**
Tahap ini tidak hanya soal menggerakkan mesin, tetapi juga membangun komunikasi dengan manusia:
* *Aksi Mekanis:* Mengirimkan sinyal perintah ke motor untuk menggerakkan lengan **Robot UR** menuju koordinat tujuan atau membuat **RoboDog** berjalan maju.


* *Aksi Komunikatif (Social Feedback):* Memberikan sinyal balik agar manusia tahu bahwa perintahnya telah diterima—misalnya melalui perubahan warna lampu indikator, bunyi *beep*, atau gerakan konfirmasi singkat.





---

### 1.2.3 Tantangan Siklus SPA saat Berinteraksi dengan Manusia

Menjalankan siklus SPA di lingkungan HRI jauh lebih menantang dibandingkan di dalam pabrik tertutup karena dua faktor utama:

1. **Manusia adalah Variabel yang Dinamis (*Unpredictable*):**
Di lini pabrik biasa, posisi benda selalu tetap dan terukur. Sebaliknya, manusia bergerak bebas—bisa tiba-tiba melangkah mendekat, mengubah gestur di tengah jalan, atau membatalkan perintah secara mendadak. Oleh karena itu, tahap *Plan* tidak boleh kaku; robot harus terus mengevaluasi ulang rencananya setiap sepersekian detik.
2. **Kecepatan Siklus (*Latency* & *Real-Time Response*):**
**Latency** adalah jeda waktu yang dibutuhkan sistem sejak kamera menangkap gambar (*Sense*), memprosesnya (*Plan*), hingga motor mulai bergerak (*Act*). Dalam HRI, latensi yang terlalu tinggi sangat berisiko. Bayangkan jika kamu memberi gestur tangan untuk menghentikan robot (*STOP*), tetapi karena pemrosesan AI terlalu lambat, robot baru berhenti 2 detik kemudian. Oleh sebab itu, efisiensi algoritma deteksi dan komunikasi data sangat krusial agar robot mampu merespons secara *real-time*.

> **[PLACEHOLDER GAMBAR 1.6: Ilustrasi Dampak Latency pada HRI]**
> *Deskripsi Ilustrasi: Perbandingan dua garis waktu (timeline). Baris atas (Low Latency / Real-time): Manusia angkat tangan berhenti -> jeda milidetik -> Robot langsung berhenti di jarak aman. Baris bawah (High Latency): Manusia angkat tangan berhenti -> jeda 2 detik -> Robot terlambat berhenti dan melewati batas aman.*

## 1.3 Keamanan dan Ergonomi Kolaborasi

### 1.3.1 Klasifikasi HRI Berdasarkan Jarak & Kontak

Tidak semua interaksi manusia dan robot terjadi dalam jarak yang sama. Berdasarkan seberapa dekat posisi fisik dan pembagian tugasnya, HRI dibagi menjadi empat tingkatan:

1. **Remote Interaction (Interaksi Jarak Jauh):** Manusia dan robot terpisah lokasi atau penghalang fisik. Contohnya adalah robot penjinak bom atau robot inspeksi area beracun yang dikendalikan dari ruang kontrol.
2. **Coexistence / Proximity (Koeksistensi):** Manusia dan robot berada di ruangan yang sama tanpa pagar pengaman, tetapi memiliki area kerja masing-masing dan tidak mengerjakan tugas yang sama.
3. **Cooperation (Kooperasi):** Manusia dan robot berbagi ruang kerja (*shared workspace*) dan bekerja menuju satu tujuan secara bergantian—misalnya manusia meletakkan komponen di meja, lalu **Robot UR** mengambilnya untuk dirakit.


4. **Physical Collaboration (Kolaborasi Fisik):** Terjadi kontak fisik langsung saat bekerja bersama, seperti manusia membimbing gerakan lengan robot secara manual atau saling menyerahkan objek dari tangan ke penjepit (*gripper*).

> **[PLACEHOLDER GAMBAR 1.7: Spektrum Kedekatan HRI]**
> *Deskripsi Ilustrasi: Ilustrasi 4 panel bertingkat dari kiri ke kanan: (1) Remote (terpisah dinding), (2) Coexistence (satu ruangan, meja terpisah), (3) Cooperation (satu meja, kerja bergantian), dan (4) Physical Collaboration (kontak langsung/serah terima benda).*

---

### 1.3.2 Arsitektur Zona Keselamatan (*Safety Zones*)

Ketika pagar pengaman dihilangkan, keselamatan dijaga menggunakan pagar virtual berbasis sensor dan kamera. Area di sekitar robot dibagi menjadi tiga lapisan **Safety Zones** dinamis:

* **Zona Hijau (*Safe Zone*):** Area terluar yang aman. Karena jarak manusia masih jauh, robot dapat beroperasi pada kecepatan normal dan optimal.
* **Zona Kuning (*Warning / Slowdown Zone*):** Area transisi ketika manusia mulai mendekat. Begitu kamera atau sensor mendeteksi tubuh manusia masuk ke area ini, robot otomatis menurunkan kecepatannya (*Speed Reduction*).
* **Zona Merah (*Danger / Stop Zone*):** Area kritis tepat di sekitar jangkauan gerak robot. Jika bagian tubuh manusia terdeteksi masuk ke zona ini, sistem langsung memicu **Protective Stop** (robot berhenti seketika) untuk mencegah benturan.

> **[PLACEHOLDER GAMBAR 1.8: Diagram Top-Down Safety Zones]**
> *Deskripsi Ilustrasi: Tampak atas (bird's-eye view) Robot UR atau RoboDog yang dikelilingi tiga lingkaran konsentris berwarna Merah (Stop), Kuning (Slowdown), dan Hijau (Normal), lengkap dengan ikon siluet manusia di tiap zona.*

---

### 1.3.3 Standar & Mekanisme Keselamatan Kolaboratif (ISO/TS 15066)

Agar robot kolaboratif (*Cobot*) seperti **Robot UR** aman bekerja di dekat manusia, perancangannya mengacu pada standar internasional **ISO/TS 15066**. Standar ini mengatur empat mekanisme perlindungan utama:

1. **Safety-Rated Monitored Stop:** Robot otomatis berhenti total saat manusia masuk ke area kolaborasi, dan baru melanjutkan geraknya setelah manusia keluar dari area tersebut.
2. **Hand Guiding:** Operator bisa memegang dan menggerakkan lengan robot secara langsung dengan tangan untuk mengajarkan titik posisi tertentu tanpa perlu menulis kode koordinat.
3. **Speed and Separation Monitoring (SSM):** Robot terus memantau jaraknya dengan manusia secara *real-time* (misalnya lewat *Pose Detection*), lalu menyesuaikan kecepatannya—semakin dekat manusia, semakin lambat gerakan robot.
4. **Power and Force Limiting (PFL):** Desain bodi robot dibuat membulat tanpa sudut tajam. Selain itu, tiap sendinya dilengkapi sensor torsi sehingga robot langsung berhenti dan memantul jika menyentuh tubuh manusia melebihi batas tekanan yang aman.

*Catatan untuk Robot Bergerak:* Pada robot berkaki seperti **RoboDog**, aspek keselamatan juga mencakup kestabilan keseimbangan agar tidak terjatuh menimpa kaki orang di sekitarnya, serta pembatasan kecepatan jalan saat berada di dalam ruangan.

> **[PLACEHOLDER GAMBAR 1.9: Empat Mode Keselamatan ISO/TS 15066]**
> *Deskripsi Ilustrasi: Infografis 4 kotak ringkas dengan ikon visual untuk masing-masing mode: (1) Monitored Stop, (2) Hand Guiding, (3) Speed & Separation Monitoring, dan (4) Power & Force Limiting.*

---

### 1.3.4 Ergonomi Fisik dan Sosial (*Proxemics*)

Sistem HRI yang baik tidak hanya sekadar aman dari tabrakan, tetapi juga harus nyaman bagi manusia secara fisik maupun psikologis:

* **Ergonomi Fisik:** Gerakan dan posisi robot harus menyesuaikan postur alami tubuh manusia. Misalnya, saat **Robot UR** menyerahkan barang (*handover*), titik serah-terimanya harus berada di ketinggian yang nyaman di depan dada/pinggang agar manusia tidak perlu membungkuk atau menjangkau terlalu tinggi.


* **Ergonomi Sosial (*Proxemics*):** Dalam psikologi sosial (teori Edward T. Hall), manusia memiliki batas "ruang personal" tak kasatmata. Robot yang tiba-tiba meluncur cepat dari arah belakang (*blind spot*) atau berhenti terlalu dekat di depan wajah akan memicu rasa kaget dan terintimidasi. Oleh karena itu, pergerakan robot idealnya datang dari arah depan atau samping yang terlihat jelas dengan kecepatan yang terasa alami.

## 1.4 Skenario Aplikatif HRI di Dunia Nyata

Penerapan HRI tidak lagi sebatas konsep fiksi ilmiah, melainkan sudah hadir di berbagai sektor—mulai dari lini produksi pabrik hingga ruang riset kampus. Berikut lima contoh nyata penerapannya:

1. **Perakitan Kolaboratif di Pabrik (*Collaborative Assembly*)**
Lengan robot seperti Universal Robots (UR) bekerja berdampingan di satu meja dengan pekerja pabrik. Robot menangani tugas berulang atau mengangkat komponen berat dengan presisi tinggi, sementara pekerja fokus pada perakitan kabel kecil atau pengecekan detail yang membutuhkan ketelitian manusia.
2. **Riset AI & Interaksi Multimodal di Kampus**
Di laboratorium robotika, platform seperti Robot UR dan RoboDog digunakan oleh peneliti dan mahasiswa untuk menguji integrasi *Computer Vision* dan *Large Language Models* (LLM). Tujuannya adalah melatih robot agar mampu memahami perintah bahasa alami maupun gestur tubuh manusia secara langsung.


3. **Inspeksi Lapangan & Area Berbahaya**
Robot berkaki empat seperti RoboDog dimanfaatkan untuk menyusuri lokasi konstruksi, area pertambangan, atau zona pascabencana yang berisiko tinggi bagi keselamatan manusia. Operator cukup mengawasi kondisi lapangan dan memberikan instruksi arah dari jarak aman.
4. **Pemantauan Keselamatan & Kesehatan Lansia (*Healthcare*)**
Robot asisten di rumah atau fasilitas perawatan lansia dilengkapi kamera *Posture Detection* untuk memantau kondisi penghuni secara non-invasif. Jika sistem mendeteksi seseorang terjatuh, robot dapat segera mendekat dan otomatis menghubungi bantuan medis.
5. **Layanan Publik & Hospitalitas**
Robot pemandu informasi di bandara maupun robot pengantar makanan di restoran dirancang agar mampu mendeteksi keberadaan pengunjung di jalurnya, berhenti secara sopan saat berpapasan, serta merespons lambaian tangan atau sapaan pengunjung.

> **[PLACEHOLDER GAMBAR 1.10: Contoh Aplikasi Nyata HRI di Berbagai Bidang]**
> *Deskripsi Ilustrasi: Kolase 5 panel ringkas: (1) Lengan UR merakit komponen bersama pekerja pabrik, (2) Mahasiswa menguji RoboDog dan UR di laboratorium kampus, (3) RoboDog berjalan melakukan inspeksi di area konstruksi, (4) Robot asisten mendeteksi lansia terjatuh di rumah, dan (5) Robot pengantar makanan menyapa pengunjung restoran.*

---

### Penutup Bab 1

Lewat Bab 1 ini, kita telah memahami bahwa robot bekerja melalui siklus berkelanjutan **Sense – Plan – Act**, serta mengapa aspek psikologi (*trust* dan beban kognitif) maupun aturan keselamatan (*safety zones* dan standar ISO/TS 15066) menjadi fondasi wajib ketika robot berbagi ruang fisik dengan manusia.

Sistem yang akan kamu bangun pada sesi praktikum nanti—mulai dari mendeteksi pose tubuh lewat kamera hingga mengirimkan perintah ke **Robot UR**, **RoboDog**, dan mengintegrasikan **LLM**—merupakan prototipe skala kecil dari berbagai aplikasi dunia nyata tersebut.

Pada **Bab 2**, kita akan membedah tahap pertama dari siklus *Sense* secara lebih teknis: bagaimana kamera dan algoritma **Pose Detection** bekerja di balik layar agar robot mampu "melihat" dan memetakan posisi sendi tubuh manusia.

> **Referensi / Bahan Bacaan Bab 1:**
> * Bartneck, C., Belpaeme, T., Eyssel, F., Kanda, T., Keijsers, M., & Šabanović, S. (2020). *Human-Robot Interaction: An Introduction*. Cambridge University Press.
> * ISO/TS 15066:2016. *Robots and robotic devices — Collaborative robots*.
> * Mori, M. (1970). *The Uncanny Valley*. Energy, 7(4), 33–35.