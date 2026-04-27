"""
News Framing Analysis
Entry point aplikasi Streamlit.

File ini hanya bertanggung jawab untuk menginisialisasi konfigurasi halaman,
mengelola session state, dan mengorkestrasikan alur antara halaman-halaman
yang tersedia. Seluruh logika bisnis dan tampilan ada di dalam folder src/.
"""

import nltk
import streamlit as st
from langdetect import detect, LangDetectException

from src.analyzer import (
    analyze_article, 
    generate_comparative_report, 
    ArticleAnalysis,
    analyze_multiple_articles
)
from src.scraper import scrape_article, scrape_multiple_articles
from src.visualizer import build_keyword_graph
from src.ui.styles import apply_custom_style
from src.ui.sidebar import render_sidebar
from src.ui.landing import display_landing_page
from src.ui.results import (
    display_article_headers,
    display_framing_comparison,
    display_actor_analysis,
    display_sentiment_analysis,
)

st.set_page_config(
    layout="wide",
    page_title="News Framing Analysis",
    page_icon="📰",
)


@st.cache_resource
def _initialize_nltk():
    """Mengunduh resource NLTK yang dibutuhkan satu kali saat aplikasi pertama dijalankan."""
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)


def _initialize_session_state():
    """Memastikan semua kunci session state sudah ada sebelum aplikasi dijalankan.

    Ini mencegah AttributeError yang bisa terjadi jika callback atau komponen
    lain mencoba mengakses session state sebelum widget yang membuatnya dirender.
    """
    defaults = {
        "current_page": "Home",
        "nav_key": "🏠 Beranda",
        "selected_model": "llama-3.3-70b-versatile",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _run_analysis_page(model_name: str):
    """Merender halaman analisis framing beserta semua logika pengambilan data dan tampilannya.

    Args:
        model_name: Nama model AI yang dipilih pengguna di sidebar.
    """
    st.header("🔍 Analisis Framing")

    tab_link, tab_manual = st.tabs(["🔗 Link Berita", "✍️ Teks Manual"])
    articles_to_analyze = []

    with tab_link:
        urls_input = st.text_area(
            "Masukkan 2 hingga 3 URL berita (satu per baris)",
            height=120,
            key="urls_input_area",
            placeholder="Contoh: https://news.detik.com/...",
        )
        if st.button("📝 Analisis dari Link", type="primary"):
            urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
            if 2 <= len(urls) <= 3:
                with st.spinner("Mengekstrak berita dari link secara paralel..."):
                    scraping_results = scrape_multiple_articles(urls)
                    for i, (title, text, error) in enumerate(scraping_results):
                        if not error:
                            articles_to_analyze.append((title, text, urls[i]))
                        else:
                            st.error(f"Gagal mengambil {urls[i]}: {error}")
            else:
                st.warning("Masukkan 2 hingga 3 link berita.")

    with tab_manual:
        st.info("Gunakan mode ini jika scraping otomatis gagal. Salin dan tempel isi berita langsung ke sini.")
        col1, col2 = st.columns(2)
        with col1:
            m_title1 = st.text_input("Judul Berita 1", key="mt1")
            m_text1 = st.text_area("Isi Berita 1", height=200, key="mx1")
        with col2:
            m_title2 = st.text_input("Judul Berita 2", key="mt2")
            m_text2 = st.text_area("Isi Berita 2", height=200, key="mx2")

        if st.button("📝 Analisis Teks Manual"):
            if m_text1 and m_text2:
                articles_to_analyze.append((m_title1 or "Berita 1", m_text1, "Input Manual"))
                articles_to_analyze.append((m_title2 or "Berita 2", m_text2, "Input Manual"))
            else:
                st.warning("Isi setidaknya dua kolom berita terlebih dahulu.")

    if not articles_to_analyze:
        return

    if "GROQ_API_KEY" not in st.secrets:
        st.error("API Key Groq belum dikonfigurasi. Tambahkan di file .streamlit/secrets.toml.")
        st.stop()

    with st.spinner("Menganalisis konten secara paralel dengan AI..."):
        all_results = analyze_multiple_articles(articles_to_analyze, model_name)
    
    # Filter hasil yang error jika ada
    errors = [res for res in all_results if res.error]
    for err in errors:
        st.error(f"Penyebab: {err.error}")
    
    all_results = [res for res in all_results if not res.error]

    if len(all_results) < 2:
        st.error("Minimal dua artikel harus berhasil dianalisis untuk menampilkan perbandingan.")
        return

    st.divider()
    st.header("📰 Artikel yang Dianalisis", divider="gray")
    display_article_headers(all_results)

    tab_comparative, tab_framing, tab_actors, tab_graph = st.tabs([
        "📈 Analisis Komparatif",
        "🏗️ Struktur Framing",
        "👥 Aktor & Sentimen",
        "🕸️ Graf Kata Kunci",
    ])

    with tab_comparative:
        st.subheader("Analisis Framing Komparatif")
        # Konversi ke tuple agar kompatibel dengan st.cache_data yang membutuhkan argumen hashable
        summary = generate_comparative_report(tuple(all_results), model_name)
        st.markdown(summary)

    with tab_framing:
        st.subheader("Perbandingan Struktur Framing (Robert Entman)")
        display_framing_comparison(all_results)

    with tab_actors:
        display_actor_analysis(all_results)
        st.divider()
        display_sentiment_analysis(all_results)

    with tab_graph:
        st.subheader("Graf Hubungan Kata Kunci")
        fig = build_keyword_graph(all_results)
        if fig:
            st.pyplot(fig)
        else:
            st.info("Data tidak cukup untuk membangun graf kata kunci.")


def main():
    """Titik masuk utama aplikasi. Mengelola inisialisasi dan routing antar halaman."""
    _initialize_nltk()
    _initialize_session_state()
    apply_custom_style()

    current_page, selected_model = render_sidebar()

    if current_page == "Home":
        display_landing_page()
    elif current_page == "Analysis":
        _run_analysis_page(selected_model)


if __name__ == "__main__":
    main()
