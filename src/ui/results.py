import streamlit as st

from src.config import FRAMING_LABEL_MAP


def display_article_headers(results: list):
    """Menampilkan judul dan tautan sumber dari setiap artikel yang berhasil dianalisis.

    Ditampilkan dalam layout kolom berjajar agar pengguna dapat langsung
    melihat konteks dari setiap sumber sebelum membaca hasil analisisnya.

    Args:
        results: List berisi objek ArticleAnalysis dari semua artikel.
    """
    valid_results = [r for r in results if r.analysis_results and not r.error]
    if not valid_results:
        return

    columns = st.columns(len(valid_results))
    for i, res in enumerate(valid_results):
        with columns[i]:
            st.subheader(res.title)
            domain = res.url.split("/")[2] if "/" in res.url else res.url
            st.caption(f"Sumber: [{domain}]({res.url})")


def display_framing_comparison(results: list):
    """Menampilkan perbandingan struktur framing Entman dari setiap artikel secara berdampingan.

    Setiap dimensi framing (Definisi Masalah, Penyebab, Evaluasi Moral,
    Rekomendasi Solusi) ditampilkan dalam baris terpisah dengan warna
    yang berbeda untuk memudahkan pembacaan komparatif.

    Args:
        results: List berisi objek ArticleAnalysis dari semua artikel.
    """
    valid_results = [r for r in results if r.analysis_results and not r.error]
    if not valid_results:
        return

    color_functions = {
        "problem_definition": st.info,
        "causal_interpretation": st.warning,
        "moral_evaluation": st.error,
        "treatment_recommendation": st.success,
    }

    for label, key in FRAMING_LABEL_MAP.items():
        st.markdown(f"#### {label}")
        columns = st.columns(len(valid_results))
        for i, res in enumerate(valid_results):
            with columns[i]:
                text = res.analysis_results.get("framing", {}).get(key, "Tidak tersedia")
                display_fn = color_functions.get(key, st.info)
                display_fn(text)

    st.divider()


def display_actor_analysis(results: list):
    """Menampilkan perbandingan daftar aktor utama yang teridentifikasi di setiap artikel.

    Args:
        results: List berisi objek ArticleAnalysis dari semua artikel.
    """
    valid_results = [r for r in results if r.analysis_results and not r.error]
    if not valid_results:
        return

    st.header("Analisis Aktor", divider="gray")
    columns = st.columns(len(valid_results))
    for i, res in enumerate(valid_results):
        with columns[i]:
            st.subheader(f"Aktor di '{res.title}'")
            actors = res.analysis_results.get("actors", ["Tidak ditemukan"])
            for actor in actors:
                st.markdown(f"- {actor}")


def display_sentiment_analysis(results: list):
    """Menampilkan perbandingan hasil analisis sentimen beserta alasannya.

    Sentimen ditampilkan dengan emoji yang sesuai untuk memudahkan
    pembacaan cepat, sementara alasan diberikan sebagai teks pendukung.

    Args:
        results: List berisi objek ArticleAnalysis dari semua artikel.
    """
    valid_results = [r for r in results if r.analysis_results and not r.error]
    if not valid_results:
        return

    st.header("Analisis Sentimen", divider="gray")
    sentiment_icons = {
        "Positif": "🙂 Positif",
        "Negatif": "☹️ Negatif",
        "Netral": "😐 Netral",
    }

    columns = st.columns(len(valid_results))
    for i, res in enumerate(valid_results):
        with columns[i]:
            st.subheader(f"Sentimen di '{res.title}'")
            sentiment = res.analysis_results.get("sentiment", "Tidak diketahui")
            reason = res.analysis_results.get("sentiment_reason", "")
            st.markdown(f"### {sentiment_icons.get(sentiment, sentiment)}")
            if reason:
                st.caption(f"Alasan: {reason}")
