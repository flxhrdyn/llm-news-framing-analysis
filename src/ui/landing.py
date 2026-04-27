import streamlit as st


def display_landing_page():
    """Merender halaman beranda aplikasi.

    Halaman ini menampilkan judul aplikasi, penjelasan singkat tentang
    metodologi framing Robert Entman, daftar fitur utama, dan tombol
    untuk langsung memulai analisis. Mengklik tombol akan memperbarui
    session state dan me-rerun aplikasi menuju halaman analisis.
    """
    st.markdown("""
        <h1 class="landing-title">
            <span style="-webkit-text-fill-color: initial;">📰</span>
            <span> News Framing Analysis</span>
        </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
        Aplikasi ini menggunakan model **Llama 3.1 & 3.3 via Groq** untuk menganalisis dan membandingkan
        bagaimana berbagai media online membingkai (**framing**) sebuah isu berdasarkan teori
        **Robert Entman (1993)**.
    """)

    st.markdown("""
    <div class="theory-card">
        <h4>Metodologi Robert Entman (1993)</h4>
        <p>Model ini mengidentifikasi bagaimana media menyeleksi aspek realitas melalui empat fungsi utama:</p>
        <ul style="line-height: 1.6;">
            <li><strong>Definisi Masalah (Problem Definition):</strong> Apa yang dianggap sebagai masalah utama dalam narasi?</li>
            <li><strong>Penyebab Masalah (Causal Interpretation):</strong> Siapa atau apa yang dianggap sebagai penyebab atau aktor di balik isu tersebut?</li>
            <li><strong>Penilaian Moral (Moral Evaluation):</strong> Bagaimana penilaian etika atau 'pahlawan vs penjahat' diterapkan?</li>
            <li><strong>Rekomendasi Solusi (Treatment Recommendation):</strong> Apa solusi yang ditawarkan atau diimplikasikan oleh media?</li>
        </ul>
        <hr style="border: 0.5px solid #444; margin: 1rem 0;">
        <p style="font-size: 0.85rem; color: #aaa;">Sumber: <a href="https://fbaum.unc.edu/teaching/articles/J-Communication-1993-Entman.pdf" target="_blank" style="color: #2A35D1;">Entman, R.M., 1993. Framing: Towards clarification of a fractured paradigm.</a></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        **Fitur Utama Analisis:**
        - **Identifikasi Framing Otomatis:** Bedah teks berita secara mendalam dalam hitungan detik.
        - **Pemetaan Aktor Utama:** Deteksi tokoh, kelompok, atau lembaga yang paling berpengaruh.
        - **Analisis Sentimen dan Keyword:** Memahami nada pemberitaan dan kata kunci yang mendominasi narasi.
        - **Graf Hubungan Media:** Visualisasi keterkaitan antar media berdasarkan kesamaan kata kunci.
    """)

    st.info("Kecepatan tinggi didukung oleh Llama 3 via Groq untuk efisiensi analisis data besar.")

    if st.button("Mulai Analisis Sekarang →"):
        st.session_state["current_page"] = "Analysis"
        st.rerun()
