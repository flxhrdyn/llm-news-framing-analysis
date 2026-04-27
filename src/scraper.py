import requests
import re
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from bs4 import BeautifulSoup

from src.config import MAX_ARTICLE_WORDS


# Header HTTP yang meniru perilaku browser sungguhan.
# Ini diperlukan karena banyak situs berita menolak permintaan dari bot
# yang tidak memiliki header yang valid.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
}

# Kata kunci yang menandakan paragraf bukan bagian dari isi berita,
# melainkan tautan promosi atau rekomendasi artikel lain.
_GARBAGE_KEYWORDS = [
    "baca juga", "simak juga", "link terkait",
    "klik di sini", "tonton video", "berita terkait",
]

# CSS selector yang umum digunakan oleh situs berita Indonesia
# untuk membungkus konten artikel utama.
_ARTICLE_SELECTORS = [
    "article",
    "div[class*='article-body']",
    "div[class*='post-content']",
    "div[class*='main-content']",
    "div[class*='story-body']",
    "div[class*='rich-text-article-body']",
    "div[id*='article-body']",
    "div.read__content",
    "div.detail__body-text",
    "div.article-content",
    "div.entry-content",
    "div[class*='content-article']",
]


@st.cache_data(ttl=3600, show_spinner="Mengekstrak teks dari URL...")
def scrape_article(url: str) -> tuple[str, str, str | None]:
    """Mengambil judul dan isi artikel dari sebuah URL berita.

    Fungsi ini melakukan permintaan HTTP, membersihkan HTML dari elemen
    yang tidak relevan seperti iklan dan navigasi, lalu mengekstrak
    paragraf isi berita. Hasilnya dipotong agar tidak melebihi batas
    token API Groq.

    Args:
        url: Alamat URL artikel berita yang ingin di-scrape.

    Returns:
        Sebuah tuple berisi (judul, teks_artikel, pesan_error).
        Jika berhasil, pesan_error akan bernilai None.
        Jika gagal, judul dan teks akan berisi pesan diagnostik
        dan pesan_error akan berisi detail kesalahannya.
    """
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        session = requests.Session()
        response = session.get(url.strip(), headers=_BROWSER_HEADERS, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Buang elemen yang tidak membawa konten seperti skrip, navigasi, dan footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "button", "noscript"]):
            tag.decompose()

        # Buang elemen yang teridentifikasi sebagai iklan atau konten promosi
        for ad in soup.select("div[class*='ads'], div[class*='promo'], div[class*='recommendation'], div[class*='related'], div[id*='google_ads']"):
            ad.decompose()

        title = _extract_title(soup)
        article_text = _extract_body(soup)

        if not article_text.strip() or len(article_text.split()) < 30:
            page_title = soup.title.string if soup.title else "Tidak Ada Judul"
            word_count = len(article_text.split())
            raise ValueError(
                f"Scraping gagal. Hanya ditemukan {word_count} kata. "
                f"Judul halaman: '{page_title}'. "
                "Kemungkinan situs ini memblokir bot atau konten dirender via JavaScript."
            )

        return title, article_text, None

    except requests.exceptions.HTTPError as e:
        msg = f"Situs menolak akses. Status HTTP {e.response.status_code} untuk URL: {e.request.url}"
        st.error(f"DEBUG: {msg}")
        return "Gagal Ekstraksi", "", msg

    except requests.exceptions.RequestException as e:
        msg = f"Gagal terhubung ke URL. Jenis error: {type(e).__name__}"
        st.error(f"DEBUG: {msg}")
        return "Gagal Ekstraksi", "", msg

    except Exception as e:
        msg = f"Terjadi kesalahan saat memproses halaman. Jenis error: {type(e).__name__}. Detail: {str(e)}"
        st.error(f"DEBUG: {msg}")
        return "Gagal Ekstraksi", "", msg


def _extract_title(soup: BeautifulSoup) -> str:
    """Mengekstrak judul artikel dari elemen HTML yang paling relevan.

    Mencoba menemukan elemen h1 terlebih dahulu, lalu fallback ke
    tag <title> jika tidak ditemukan. Nama situs di akhir judul
    (dipisahkan oleh ' - ', ' | ', atau ' : ') akan dihapus.
    """
    title_tag = soup.find(["h1", "h2"])
    if title_tag:
        raw_title = title_tag.get_text(strip=True)
    elif soup.title:
        raw_title = soup.title.get_text(strip=True)
    else:
        return "Judul Tidak Ditemukan"

    return re.split(r" - | \| | : ", raw_title)[0].strip()


def _extract_body(soup: BeautifulSoup) -> str:
    """Mengekstrak teks isi artikel dari elemen konten yang relevan.

    Mencoba menemukan kontainer artikel menggunakan daftar CSS selector
    yang umum dipakai situs berita. Jika tidak ditemukan, akan mencari
    di seluruh halaman sebagai fallback. Paragraf yang terdeteksi
    sebagai iklan atau terlalu pendek akan dibuang.

    Teks akhir dipotong di batas MAX_ARTICLE_WORDS kata untuk menjaga
    agar permintaan ke API Groq tidak melebihi batas token.
    """
    container = next(
        (soup.select_one(s) for s in _ARTICLE_SELECTORS if soup.select_one(s)),
        None,
    )
    search_area = container if container else soup

    paragraphs = search_area.find_all(["p", "div", "span"])
    clean_paragraphs = []

    for p in paragraphs:
        text = p.get_text(strip=True)
        is_long_enough = len(text.split()) > 8
        is_not_garbage = not any(kw in text.lower() for kw in _GARBAGE_KEYWORDS)

        if is_long_enough and is_not_garbage:
            clean_paragraphs.append(text)

    # Hapus paragraf duplikat yang sering muncul di situs berita
    clean_paragraphs = list(dict.fromkeys(clean_paragraphs))
    article_text = "\n\n".join(clean_paragraphs)

    # Fallback jika hasil ekstraksi paragraf terlalu sedikit
    if len(article_text.split()) < 50:
        article_text = re.sub(r"\s+", " ", search_area.get_text(" ", strip=True))

    words = article_text.split()
    if len(words) > MAX_ARTICLE_WORDS:
        article_text = " ".join(words[:MAX_ARTICLE_WORDS]) + "... [Teks dipotong karena melebihi batas panjang API]"

    return article_text


def scrape_multiple_articles(urls: list[str]) -> list[tuple[str, str, str | None]]:
    """Mengambil teks dari beberapa URL secara paralel.

    Args:
        urls: List berisi URL berita.

    Returns:
        List berisi tuple (judul, teks, error) untuk setiap URL.
    """
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        results = list(executor.map(scrape_article, urls))
    return results
