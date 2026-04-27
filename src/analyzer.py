import json
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from groq import Groq
from langdetect import detect, LangDetectException

from src.config import (
    AVAILABLE_MODELS,
    FRAMING_SYSTEM_PROMPT,
    COMPARATIVE_SYSTEM_PROMPT,
)
from src.scraper import scrape_article
from src.models import AnalysisResultModel


# Struktur data yang menyimpan semua informasi hasil analisis untuk satu artikel.
# Menggunakan namedtuple agar kode yang mengaksesnya lebih ekspresif
# dibandingkan menggunakan dictionary biasa.
ArticleAnalysis = namedtuple(
    "ArticleAnalysis",
    ["url", "title", "text", "analysis_results", "error", "lang"],
)


def get_groq_client() -> Groq | None:
    """Membuat dan mengembalikan instance Groq client yang sudah terkonfigurasi.

    API key diambil dari secrets Streamlit (untuk deployment) atau dari
    session state (jika pengguna memasukkan key secara manual di UI).

    Returns:
        Instance Groq client jika API key ditemukan, atau None jika tidak.
    """
    api_key = st.secrets.get("GROQ_API_KEY") or st.session_state.get("custom_groq_key")
    if not api_key:
        return None
    return Groq(api_key=api_key)


@st.cache_data(ttl=3600, show_spinner="Menganalisis framing, aktor, dan sentimen...")
def analyze_article(article_text: str, model_name: str) -> dict:
    """Menganalisis satu artikel berita menggunakan model AI Groq.

    Mengirimkan teks artikel ke model yang dipilih dan meminta analisis
    dalam tiga dimensi: framing Entman, identifikasi aktor, dan sentimen.
    Hasilnya dikembalikan sebagai dictionary Python yang sudah di-parse
    dari format JSON.

    Args:
        article_text: Teks bersih dari artikel yang akan dianalisis.
        model_name: Nama model Groq yang akan digunakan (misal: 'llama-3.3-70b-versatile').

    Returns:
        Dictionary berisi hasil analisis dengan kunci 'framing', 'actors',
        'sentiment', dan 'sentiment_reason'. Jika terjadi kesalahan,
        dictionary akan berisi kunci 'error' dengan pesan deskriptif.
    """
    client = get_groq_client()
    if not client:
        return {"error": "API Key Groq tidak ditemukan. Pastikan sudah dikonfigurasi di secrets.toml."}

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": FRAMING_SYSTEM_PROMPT},
                {"role": "user", "content": article_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        # Validasi hasil JSON menggunakan Pydantic
        raw_json = completion.choices[0].message.content
        validated_data = AnalysisResultModel.model_validate_json(raw_json)
        
        # Kembalikan sebagai dict agar kompatibel dengan kode UI yang sudah ada
        return validated_data.model_dump()

    except Exception as e:
        return {"error": f"Gagal memvalidasi hasil analisis: {str(e)}"}


@st.cache_data(ttl=3600, show_spinner="Membuat laporan analisis komparatif...")
def generate_comparative_report(results: tuple, model_name: str) -> str:
    """Membuat laporan analisis komparatif dari beberapa hasil analisis artikel.

    Mengambil data framing dari semua artikel yang berhasil dianalisis,
    lalu meminta model AI untuk menyusun laporan perbandingan yang formal
    dan terstruktur.

    Args:
        results: Tuple berisi objek ArticleAnalysis dari beberapa artikel.
                 Menggunakan tuple (bukan list) karena st.cache_data
                 memerlukan argumen yang bisa di-hash.
        model_name: Nama model Groq yang akan digunakan.

    Returns:
        String berisi laporan komparatif dalam format Markdown,
        atau pesan error jika proses gagal.
    """
    valid_results = [r for r in results if r.analysis_results and not r.error]
    if len(valid_results) < 2:
        return "Analisis komparatif membutuhkan setidaknya dua artikel yang berhasil dianalisis."

    client = get_groq_client()
    if not client:
        return "API Key Groq tidak ditemukan."

    # Susun konteks dari semua hasil analisis menjadi teks yang mudah dibaca oleh model
    context_parts = []
    for res in valid_results:
        source_name = res.url.split("/")[2].replace("www.", "") if "/" in res.url else res.url
        framing = res.analysis_results.get("framing", {})
        framing_text = "\n".join(f"{k}: {v}" for k, v in framing.items())
        context_parts.append(f"Sumber: {source_name} ({res.title})\n{framing_text}")

    context = "\n\n---\n\n".join(context_parts)
    user_prompt = f"Buatlah laporan analisis komparatif berdasarkan data framing berikut:\n\n{context}"

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": COMPARATIVE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Gagal membuat laporan komparatif: {str(e)}"


def run_analysis_pipeline(url: str, model_name: str) -> ArticleAnalysis:
    """Menjalankan pipeline lengkap dari URL hingga hasil analisis untuk satu artikel.

    Ini adalah fungsi orkestrasi yang menggabungkan proses scraping,
    deteksi bahasa, dan analisis AI dalam satu langkah. Cocok digunakan
    ketika input berasal dari URL.

    Args:
        url: Alamat URL artikel berita.
        model_name: Nama model Groq yang akan digunakan untuk analisis.

    Returns:
        Objek ArticleAnalysis yang berisi semua informasi artikel dan
        hasil analisisnya. Jika terjadi kesalahan di tahap mana pun,
        field 'error' akan terisi dan field 'analysis_results' akan None.
    """
    title, text, scrape_error = scrape_article(url)
    lang = "indonesian"

    if scrape_error:
        return ArticleAnalysis(url, title, text, None, f"Gagal mengekstrak konten: {scrape_error}", lang)

    try:
        lang_code = detect(text)
        if lang_code == "en":
            lang = "english"
    except LangDetectException:
        pass

    analysis_results = analyze_article(text, model_name)
    if "error" in analysis_results:
        return ArticleAnalysis(url, title, text, None, f"Gagal menganalisis konten: {analysis_results['error']}", lang)

    return ArticleAnalysis(url, title, text, analysis_results, None, lang)


def analyze_multiple_articles(articles: list[tuple], model_name: str) -> list[ArticleAnalysis]:
    """Menganalisis beberapa artikel secara paralel menggunakan ThreadPoolExecutor.

    Args:
        articles: List berisi tuple (judul, teks, url).
        model_name: Nama model Groq yang digunakan.

    Returns:
        List berisi objek ArticleAnalysis untuk setiap artikel.
    """
    def _task(article_data):
        title, text, url = article_data
        
        # Deteksi bahasa (dilakukan di dalam thread agar tidak blocking)
        lang = "indonesian"
        try:
            from langdetect import detect
            if detect(text) == "en":
                lang = "english"
        except:
            pass
            
        analysis = analyze_article(text, model_name)
        if "error" in analysis:
            return ArticleAnalysis(url, title, text, None, f"Error: {analysis['error']}", lang)
        return ArticleAnalysis(url, title, text, analysis, None, lang)

    with ThreadPoolExecutor(max_workers=len(articles)) as executor:
        results = list(executor.map(_task, articles))
        
    return results
