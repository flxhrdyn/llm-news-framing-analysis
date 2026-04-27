# 📰 News Framing Analysis Tool

Aplikasi analisis media berbasis AI yang dirancang untuk membedah bagaimana berbagai media online membingkai (**framing**) sebuah isu berdasarkan teori **Robert Entman (1993)**.

## ✨ Fitur Utama
- **Multi-Page Architecture:** Beranda metodologis dan Workspace analisis yang terpisah.
- **Automated Framing Analysis:** Mengidentifikasi *Problem Definition*, *Causal Interpretation*, *Moral Evaluation*, dan *Treatment Recommendation* secara otomatis.
- **Actor & Sentiment Mapping:** Mendeteksi aktor utama dan nada sentimen pemberitaan.
- **Keyword Relationship Graph:** Visualisasi keterkaitan narasi antar media melalui grafik kata kunci.
- **Premium UI/UX:** Desain modern dengan sistem navigasi instan dan tampilan tabbed yang intuitif.
- **AI-Powered by Groq:** Menggunakan model Llama 3.3, Llama 3.1, dan Qwen untuk analisis cepat dan akurat.

## 🚀 Cara Menjalankan
1. Clone repositori ini.
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Konfigurasi API Key di `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "your_api_key_here"
   ```
4. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```

## 📚 Metodologi
Aplikasi ini mengacu pada empat fungsi framing menurut Robert Entman:
1. **Define Problems:** Mengidentifikasi masalah utama.
2. **Diagnose Causes:** Mengidentifikasi aktor/penyebab.
3. **Make Moral Judgments:** Mengevaluasi sisi etis narasi.
4. **Suggest Remedies:** Menawarkan solusi atau prediksi hasil.

---
*Dibuat untuk analisis komunikasi massa dan riset media digital.*
