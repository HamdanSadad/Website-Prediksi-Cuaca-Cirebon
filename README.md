# Prediksi Polusi Udara (PM2.5) Kota Cirebon dengan XGBoost

Aplikasi web cerdas (*Smart Web App*) untuk memprediksi tingkat kualitas udara (khususnya konsentrasi partikel PM2.5) di Kota Cirebon, Jawa Barat. Proyek ini memadukan model Machine Learning **XGBoost Regressor** tingkat lanjut dengan integrasi API Cuaca Otomatis (Open-Meteo) dan antarmuka web interaktif menggunakan **Flask**.

---

## 📖 Tentang Proyek

Polusi udara merupakan masalah lingkungan krusial yang berdampak langsung pada kesehatan masyarakat. Partikel debu halus PM2.5 sangat berbahaya karena dapat masuk ke aliran darah. Proyek ini dibangun untuk:
1. Menganalisis pola pergerakan dan konsentrasi PM2.5 di Kota Cirebon secara historis.
2. Membangun model prediktif berbasis algoritma pohon (Tree-Based), yaitu **XGBoost**, yang unggul dalam data tabular berstruktur.
3. Mendemonstrasikan secara langsung (melalui Web) bagaimana model dapat memprediksi tingkat polusi pada masa depan (**T+6** dan **T+24** jam ke depan) tanpa mengharuskan pengguna repot memasukkan suhu, kelembapan, curah hujan, dll secara manual.

---

## 🔄 Alur Proyek (End-to-End Workflow)

Proyek ini dikembangkan melalui siklus Data Science yang komprehensif, dari *raw data* hingga aplikasi *Production-ready*:

1. **Pengumpulan Data (Data Gathering):**
   - Mengambil data cuaca dan kualitas udara PM2.5 historis Kota Cirebon tahun 2023. Sumber data ditarik dari *Open-Meteo Archive API*.
2. **Eksplorasi Data (EDA - Exploratory Data Analysis):**
   - Melihat korelasi antar variabel iklim (suhu, kelembapan, curah hujan, kecepatan angin) terhadap konsentrasi PM2.5.
   - Mengamati tren musiman, mingguan, dan harian.
3. **Preprocessing & Penanganan Nilai Kosong (Missing Values):**
   - Membersihkan data anomali dan menggunakan teknik interpolasi (*time-based interpolation*) untuk mengisi kekosongan data yang hilang akibat kegagalan sensor historis.
4. **Rekayasa Fitur (Advanced Temporal Feature Engineering):**
   - Menambahkan banyak kolom referensi waktu (jam, hari, bulan) yang dimanipulasi dengan algoritma *Cyclical Encoding* (`sin`/`cos`) agar model paham siklus rotasi waktu.
   - Membuat *Lag Features* (cuaca 1, 3, 6, 24 jam yang lalu).
   - Membuat *Rolling Window Statistics* (Rata-rata atau Maksimum cuaca selama 24 jam terakhir).
5. **Pemodelan & Tuning (Modeling with XGBoost):**
   - Melatih model regresi berbasis *Extreme Gradient Boosting*.
   - Melakukan optimasi hyperparameter (*Tuning*) menggunakan pustaka **Optuna** untuk mencari kombinasi parameter terhebat.
6. **Deployment (Web Application):**
   - Mengekspor model final yang sudah matang ke format biner `.pkl` (Pickle).
   - Membangun antarmuka pengguna berbasis HTML/CSS/JS modern.
   - Mengembangkan sistem otomasi API di *backend* Python Flask, di mana pengguna cukup memilih "Tanggal" dan mesin yang akan melakukan semua pekerjaan.

---

## 🔬 Analisis: Mengapa Menggunakan "Temporal Feature Engineering" pada XGBoost?

Model XGBoost pada dasarnya **bukanlah model Time-Series murni** (seperti ARIMA atau LSTM). XGBoost tidak memiliki "memori" internal untuk mengingat data masa lalu. XGBoost menganggap setiap baris data bersifat independen. 

Untuk mensiasati hal ini pada studi kasus polusi Cirebon, kita **wajib** melakukan *Temporal Feature Engineering*. Analisis peranannya:

*   **Pentingnya *Lag Features* (Data Terdahulu):** Kondisi udara tidak berubah instan. PM2.5 jam 12 siang sangat dipengaruhi oleh PM2.5 jam 11 siang (`lag_1`). Tanpa fitur ini, XGBoost buta terhadap momentum tren.
*   **Pentingnya *Rolling Window*:** Hujan deras selama 6 jam terakhir (`rolling_mean_curah_hujan_6`) secara drastis akan membersihkan PM2.5 dari udara ("washout effect"). Jika kita hanya memberi informasi hujan "saat ini", XGBoost akan luput membaca sejarah akumulasi basah tersebut.
*   **Pentingnya *Cyclical Encoding* (Sin/Cos Waktu):** Kualitas udara Cirebon sangat terpaku pada siklus. Siang polusi tinggi karena kendaraan bermotor, malam relatif rendah. Dengan mengubah jam (0-23) menjadi `sin(hour)` dan `cos(hour)`, XGBoost bisa memahami bahwa jam 23:00 malam itu jaraknya sangat dekat dengan jam 01:00 dini hari (sebuah siklus melingkar, bukan garis lurus).

**Kesimpulan:** Berkat *Temporal Feature Engineering* (46 fitur turunan yang dirakit dari 5 fitur dasar), akurasi XGBoost untuk memprediksi horison T+6 dan T+24 di Cirebon meningkat secara signifikan, mampu menangkap pola lonjakan (spike), dan menghasilkan *error* RMSE yang jauh lebih kecil.

---

## 🚀 Cara Menjalankan Aplikasi Web

Ikuti panduan berikut untuk memasang (*install*) dan menjalankan proyek ini di komputer Anda:

### 1. Persyaratan Sistem
Pastikan komputer Anda sudah terinstal:
- **Python 3.8+** atau lebih baru
- Internet aktif (untuk sistem otomasi penarikan API Open-Meteo)

### 2. Instalasi Library (Pustaka Python)
Buka terminal (CMD / PowerShell / Terminal VSCode) di dalam folder proyek ini, lalu jalankan perintah instalasi menggunakan file `requirements.txt`:

```bash
pip install -r requirements.txt
```

*(Catatan: Ini akan menginstal Flask, Pandas, Numpy, XGBoost, Scikit-Learn, Joblib, dan Requests).*

### 3. Cara Menjalankan Server Lokal
Setelah instalasi selesai, pastikan Anda berada di direktori proyek, lalu jalankan perintah:

```bash
python app.py
```

Jika berhasil, terminal akan menampilkan teks seperti:
`* Running on http://127.0.0.1:5000`

### 4. Menggunakan Aplikasi
1. Buka browser (Chrome/Edge/Firefox).
2. Akses alamat: **`http://127.0.0.1:5000`**
3. Di halaman web, Anda akan melihat **Form Input Prediksi Otomatis**.
4. Cukup ubah/pilih **Tanggal & Jam Pengamatan**.
5. Klik tombol besar berwarna biru: **"Ambil Data & Prediksi Sekarang"**.
6. Selesai! Web akan mengambil kondisi parameter meteorologi otomatis dari satelit lalu meramalkan tren tingkat polusi PM2.5 dalam 6 jam dan 24 jam ke depan menggunakan *Artificial Intelligence*.

---

## 📂 Struktur Direktori & File Proyek

Proyek ini menggunakan arsitektur *Client-Server* sederhana yang dibangun di atas *Framework Web Backend* **Flask (Python)** dan antarmuka *Frontend* menggunakan HTML, CSS (Vanilla), dan Javascript murni. 

Berikut adalah rincian isi folder `tugas-gilang`:

```text
tugas-gilang/
│
├── 📓 Data_PM25_Kota_Cirebon.ipynb           # Notebook untuk proses penarikan raw data PM2.5 dari API Open-Meteo
├── 📓 Eksperimen_2_1_Forecasting_PM2_5...    # Notebook untuk proses EDA, Preprocessing, Feature Engineering, hingga Modeling XGBoost & Optuna
│
├── ⚙️ app.py                                 # File UTAMA Backend (Server Flask). Menangani routing Web, pemanggilan API satelit, manipulasi 46 fitur, dan fungsi Prediksi XGBoost.
├── 📄 requirements.txt                       # Daftar pustaka (library) Python beserta versinya yang dibutuhkan untuk menjalankan aplikasi.
├── 📖 README.md                              # Dokumentasi inti proyek yang sedang Anda baca saat ini.
│
├── 📂 models/                                # Folder penyimpanan model Machine Learning (AI)
│   ├── 🧠 xgbfullt6.pkl                      # File model XGBoost yang telah dilatih untuk memprediksi PM2.5 dalam horison T+6 (6 jam ke depan)
│   └── 🧠 xgbfullt24.pkl                     # File model XGBoost yang telah dilatih untuk memprediksi PM2.5 dalam horison T+24 (24 jam ke depan)
│
├── 📂 static/                                # Folder untuk aset statis Frontend (Desain & Logika UI)
│   ├── 📂 css/
│   │   └── 🎨 main.css                       # File styling (CSS murni) untuk membuat tampilan UI web yang modern, responsif, dan elegan
│   └── 📂 js/
│       └── 📜 main.js                        # File logika Frontend (Javascript). Menangani aksi klik tombol otomatisasi dan manipulasi pembaruan Chart prediksi di layar
│
└── 📂 templates/                             # Folder untuk struktur kerangka tampilan web (HTML)
    ├── 🖼️ base.html                          # Layout dasar/kerangka utama HTML (Navbar, Footer, impor Font & CSS)
    └── 🖼️ index.html                         # Halaman beranda utama yang menampung Form Input, Hasil Prediksi, dan Grafik Chart
```

### 💻 Teknologi & Framework yang Digunakan:
- **Backend**: Python 3, Flask, Pandas, Numpy, Requests.
- **Machine Learning**: XGBoost, Scikit-Learn, Joblib, Optuna (saat riset).
- **Frontend**: HTML5, CSS3, Vanilla Javascript, Chart.js (untuk visualisasi grafik).

---
*Dibuat untuk tujuan edukasi dan eksperimen pemodelan lingkungan.*
