#  UTS Graf Sains Data — E-Commerce Graph Recommendation System

Repositori ini berisi penyelesaian Ujian Tengah Semester (UTS) Mata Kuliah **Graf Sains Data**, Program Studi S1 Sains Data, Universitas Negeri Surabaya (UNESA).

---

## Identitas

* **Nama**  : Gesang Nur Zamroji
* **NIM**   : 23031554145
* **Kelas** : 2023 D
* **Email** : datascience@unesa.ac.id

---

## Deskripsi Proyek

Proyek ini mengimplementasikan pemodelan Graf Properti (Property Graph) menggunakan **Neo4j** dan **Python Driver** pada dataset e-commerce **RetailRocket**. Proyek ini mencakup:

1. **Data Wrangling & Time-based Filtering**: Pemisahan interaksi berdasarkan dua periode waktu ($P_1$ untuk Training dan $P_2$ untuk Testing).
2. **Bulk Data Import**: Mengimpor jutaan baris data ke Neo4j menggunakan batch processing (Cypher `UNWIND` & `CALL`).
3. **Exploratory Data Analysis (EDA)**: Analisis komposisi subgraph (Node & Relationship).
4. **Vector Space Modelling (VSM)**: Representasi matriks *sparse* (CSR) untuk User & Item serta visualisasi jaringan bipartit menggunakan `NetworkX` dan `Matplotlib`.
5. **Graph Similarity & Recommendation**: Perhitungan kemiripan (Cos/Jaccard Similarity), penentuan $k$-NN, serta evaluasi sistem rekomendasi menggunakan metrik **Hit@5** dan **NDCG@5**.

---

## Struktur Direktori

```text
.
├── data/
│   ├── raw/
│   │   └── events.csv               # Dataset asli dari Kaggle RetailRocket
│   └── processed/
│       ├── train_P1.csv             # Data Filtered Periode P1 (Training)
│       ├── test_P2.csv              # Data Filtered Periode P2 (Testing)
│       └── events_filtered.csv      # Data Gabungan P1 & P2
├── import_retailrocket.py           # Script Python untuk impor data batch ke Neo4j
├── notebook.ipynb                   # Jupyter Notebook dokumentasi & analisis lengkap
├── requirements.txt                 # Dependensi proyek
└── README.md                        # Dokumentasi proyek
```

---

## Persiapan & Instalasi Environment

### 1. Membuat & Mengaktifkan Virtual Environment
Gunakan `venv` atau `uv` (diuji dengan Python 3.10.7):

* **Menggunakan `venv`:**
  ```bash
  python -m venv myenv
  source myenv/bin/activate        # Linux/MacOS
  # myenv\Scripts\activate         # Windows PowerShell
  ```

* **Menggunakan `uv`:**
  ```bash
  uv venv myvenv --python 3.10
  source myvenv/bin/activate
  ```

### 2. Install Dependensi
Jalankan perintah berikut untuk mengunduh library yang dibutuhkan:

```bash
pip install -r requirements.txt
# atau jika menggunakan uv:
uv pip install -r requirements.txt
```

---

## Langkah Impor Data ke Neo4j

Sebelum menjalankan script impor, pastikan instance Neo4j Database Anda sudah berjalan.

Jalankan script `import_retailrocket.py` dengan memberikan parameter koneksi dan password database:

```bash
python scripts/import_retailrocket.py -u neo4j -p PASSWORD_NEO4J_ANDA -b neo4j://localhost:7687 --database utsretailrocket --batch-size 1000
```

> **Catatan:** Script secara otomatis akan membuat *Uniqueness Constraint* pada `Visitor(visitorId)` dan `Item(itemId)` sebelum memasukkan hubungan (`VIEWED`, `ADDED_TO_CART`, `BOUGHT`).

---

## Ringkasan Jawaban & Analisis UTS

### 1. Tugas Pendahuluan (Checkpoint)
1. **Nama Database:** `neo4j` (atau disesuaikan dengan database custom seperti `utsretailrocket`).
2. **Akses Database Lain:** Menggunakan klausa Cypher `SHOW DATABASES`, `USE nama_database`, atau menentukan parameter `database_` pada Python Driver API.
3. **Jenis Graf Pertemanan:** *Directed Property Graph* (Graf Properti Berarah) dengan node berlabel `Person` dan edge `KNOWS`.

### 2. Wrangling & EDA

#### 2.1 Penentuan Periode Filtering ($P_1$ & $P_2$)
Dataset dibatasi pada rentang waktu interaksi unik berikut:
* $P_1$ (Training): 2015-07-25 s.d. 2015-08-07 (14 Hari) → 306,731 interaksi.
* $P_2$ (Testing) : 2015-08-08 s.d. 2015-08-14 (7 Hari) → 118,822 interaksi.
* **Total Terfilter:** 425,553 interaksi.

#### 2.2 Komposisi Subgraph pada Neo4j
Menggunakan query Cypher via Python API:
* **Jumlah Node** (Total: 333,163):
  * `Visitor`: 236,530 node
  * `Item`: 96,633 node
* **Jumlah Relationship** (Total: 425,553):
  * `VIEWED`: 411,376
  * `ADDED_TO_CART`: 10,758
  * `BOUGHT`: 3,419

#### 2.3 Vector Space Modelling (VSM) User & Item
* **VSM User Matrix** (Shape: $169,351 \times 79,085$):
  * Dimensi per User: 79,085 item.
  * Density: 0.001827% | Sparsity: 99.998173%.
* **VSM Item Matrix** (Shape: $79,085 \times 169,351$): Proyeksi berlawanan berukuran matriks terisolasi.
* **Proyeksi Efektif/Efisien:** Proyeksi berbasis User Vector Space (Item-based filtering/Collaborative) maupun Item Projections dioptimalkan menggunakan format Compressed Sparse Row (CSR) untuk efisiensi alokasi RAM (< 2 MB).

### 3. Analytics & Recommendation System

#### 3.1 Rekomendasi $k$-NN ($k = 5$)
* Seorang user dipilih secara acak menggunakan metode *seeded random sampling* agar dapat direproduksi (*reproducible*).
* Menghitung nilai kemiripan (Cosine / Jaccard Similarity) untuk menentukan 5 tetangga terdekat ($k=5$).
* Mengekstrak item-item teratas yang diinteraksikan oleh tetangga namun belum pernah dilihat oleh user target sebagai item rekomendasi.

#### 3.2 Evaluasi Rekomendasi
Berdasarkan data uji pada periode $P_2$ (Testing), hasil evaluasi Top-5 rekomendasi memberikan performa sebagai berikut:
* **Hit@5:** Menunjukkan apakah minimal ada 1 item rekomendasi yang terbukti dibeli/dilihat oleh user pada periode $P_2$.
* **NDCG@5:** Menghitung *Normalized Discounted Cumulative Gain* untuk mengukur ketepatan urutan/peringkat rekomendasi.