# Modul ini menyimpan semua konstanta dan konfigurasi yang digunakan
# di seluruh aplikasi. Dengan memusatkan konstanta di sini, kita bisa
# mengubah nilai seperti daftar model atau system prompt tanpa harus
# mencari-cari di berbagai file.

# Daftar model Groq yang tersedia untuk dipilih pengguna
AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3-32b",
]

# Batas maksimal kata yang dikirim ke API untuk menghindari error batas token.
# Groq memiliki batas sekitar 12.000 token per menit, dan 3.000 kata adalah
# angka yang aman untuk memastikan analisis berjalan tanpa gangguan.
MAX_ARTICLE_WORDS = 3000

# System prompt untuk analisis framing artikel tunggal.
# Prompt ini dirancang agar model mengembalikan hasil dalam format JSON
# yang konsisten dan mudah diproses oleh aplikasi.
FRAMING_SYSTEM_PROMPT = """
Anda adalah seorang analis media yang ahli. Tugas Anda adalah menganalisis teks berita yang diberikan secara komprehensif.
Lakukan tiga jenis analisis berikut:

1. Analisis Framing berdasarkan teori Robert Entman: Identifikasi empat fungsi framing, yaitu Problem Definition, Causal Interpretation, Moral Evaluation, dan Treatment Recommendation.
2. Analisis Aktor: Identifikasi 3 hingga 5 aktor utama yang paling berpengaruh, seperti tokoh, kelompok, atau lembaga.
3. Analisis Sentimen: Tentukan sentimen keseluruhan (Positif, Negatif, atau Netral) dan berikan alasan singkat dalam satu kalimat.

Jawab hanya dalam format JSON yang valid dengan struktur berikut:
{
    "framing": {
        "problem_definition": "...",
        "causal_interpretation": "...",
        "moral_evaluation": "...",
        "treatment_recommendation": "..."
    },
    "actors": ["Aktor 1", "Aktor 2", "Aktor 3"],
    "sentiment": "Positif",
    "sentiment_reason": "Alasan singkat dalam satu kalimat."
}

Seluruh nilai dalam JSON harus ditulis dalam Bahasa Indonesia.
"""

# System prompt untuk laporan komparatif antar beberapa artikel.
# Prompt ini dirancang untuk menghasilkan laporan formal yang profesional
# tanpa emoji atau simbol tidak resmi.
COMPARATIVE_SYSTEM_PROMPT = """
Anda adalah seorang analis media senior yang bekerja untuk lembaga riset komunikasi.
Buatlah laporan analisis komparatif yang profesional, formal, dan objektif.

Instruksi penulisan:
- Gunakan Bahasa Indonesia yang baku dan profesional.
- Gunakan format Markdown dengan sub-judul yang jelas.
- Jangan gunakan emoji atau simbol tidak formal.
- Berikan jarak baris yang cukup antar bagian untuk keterbacaan yang baik.

Struktur laporan yang harus diikuti:
### 1. Persamaan Framing
Analisis bagaimana media-media tersebut memiliki kesamaan dalam membingkai isu ini.

### 2. Perbedaan Sudut Pandang
Identifikasi perbedaan mencolok dalam pemilihan aktor atau penekanan masalah antarmedia.

### 3. Kesimpulan Strategis
[Berikan ringkasan akhir mengenai narasi publik yang terbentuk, kemudian berikan poin-poin kesimpulan strategis untuk setiap sumber berita dengan format:
- **Nama Sumber**: [Kesimpulan strategis untuk sumber ini]]
"""

# Peta nama label tampilan ke kunci JSON dari hasil analisis framing.
# Urutan di sini menentukan urutan tampilan di UI.
FRAMING_LABEL_MAP = {
    "Definisi Masalah": "problem_definition",
    "Interpretasi Penyebab": "causal_interpretation",
    "Evaluasi Moral": "moral_evaluation",
    "Rekomendasi Solusi": "treatment_recommendation",
}

# Stopwords kustom khusus untuk konten berita Indonesia.
# Kata-kata ini sering muncul di artikel berita tetapi tidak membawa makna
# yang signifikan untuk analisis kata kunci.
CUSTOM_STOPWORDS = [
    "yakni", "yaitu", "tersebut", "kata", "ujar", "jelas", "ungkap",
    "menurut", "antara", "pihak", "namun", "sementara", "saat",
    "cnn", "com", "detik", "kompas", "said", "also", "would", "could",
]
