import streamlit as st
import requests
from bs4 import BeautifulSoup as bs
import re
import json
import time
from collections import namedtuple, Counter
import networkx as nx
import matplotlib.pyplot as plt
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from langdetect import detect, LangDetectException
from groq import Groq


st.set_page_config(layout="wide", page_title="Analisis Framing Berita Otomatis")

# Struktur data untuk menyimpan semua hasil analisis dari AI
ArticleAnalysis = namedtuple('ArticleAnalysis', ['url', 'title', 'text', 'analysis_results', 'error', 'lang'])

@st.cache_resource
def download_nltk_resources():
    # Mengunduh resource stopwords dari NLTK
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
download_nltk_resources()


# BUSINESS UNDERSTANDING
# (UI Header removed - replaced by Landing Page)



# DATA COLLECTION & PREPARATION
@st.cache_data(ttl=3600, show_spinner="Mengekstrak teks dari URL...")
def scrape_article(url):
    # Mengambil judul dan teks artikel dari URL
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }

        session = requests.Session()
        response = session.get(url.strip(), headers=headers, timeout=20)
        response.raise_for_status()
        
        # Menggunakan html.parser bawaan Python untuk stabilitas maksimal di semua OS
        parsing = bs(response.text, 'html.parser')
        
        # Hapus elemen yang tidak perlu agar tidak mengotori ekstraksi teks
        for redundant in parsing(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'iframe', 'button', 'noscript']):
            redundant.decompose()
        
        # Hapus elemen yang biasanya berisi iklan atau rekomendasi berdasarkan class/id
        for ads in parsing.select('div[class*="ads"], div[class*="promo"], div[class*="recommendation"], div[class*="related"], div[id*="google_ads"]'):
            ads.decompose()

        
        title_tag = parsing.find(['h1', 'post-title', 'entry-title', 'h2'])
        if not title_tag:
            title_tag = parsing.find('h1')
        
        if title_tag:
            title = title_tag.get_text(strip=True)
        elif parsing.title:
            title = parsing.title.get_text(strip=True)
        else:
            title = "Judul Tidak Ditemukan"
        
        # Bersihkan judul dari embel-embel nama situs
        title = re.split(r' - | \| | : ', title)[0]
        
        selectors = [
            'article', 'div[class*="article-body"]', 'div[class*="post-content"]',
            'div[class*="main-content"]', 'div[class*="story-body"]', 'div[class*="rich-text-article-body"]',
            'div[id*="article-body"]', 'div.read__content', 'div.detail__body-text',
            'div.article-content', 'div.entry-content', 'div[class*="content-article"]'
        ]
        
        article_container = next((parsing.select_one(s) for s in selectors if parsing.select_one(s)), None)
        search_area = article_container if article_container else parsing
        
        paragraphs = search_area.find_all(['p', 'div', 'span'])
        
        # Ekstraksi berbasis paragraf dengan filter sampah
        p_texts = []
        garbage_keywords = ['baca juga', 'simak juga', 'link terkait', 'klik di sini', 'tonton video', 'berita terkait']
        
        for p in paragraphs:
            p_text = p.get_text(strip=True)
            # Filter: panjang kata cukup, dan bukan kalimat promosi/sampah
            if len(p_text.split()) > 8:
                if not any(kw in p_text.lower() for kw in garbage_keywords):
                    p_texts.append(p_text)
        
        # Hilangkan duplikat paragraf (sering terjadi di web berita)
        p_texts = list(dict.fromkeys(p_texts))
        article_text = "\n\n".join(p_texts)
        
        # Fallback 1: Jika p_texts sedikit, coba ambil semua teks dari search_area yang terlihat seperti konten
        if len(article_text.split()) < 50:
            raw_text = search_area.get_text(" ", strip=True)
            article_text = re.sub(r'\s+', ' ', raw_text)

        # SAFETY TRUNCATION: Batasi panjang teks maksimal agar tidak kena limit 413 Groq
        # 12.000 token biasanya setara ~9.000 kata. Kita batasi di 3.000 kata agar aman dan hemat kuota.
        words = article_text.split()
        if len(words) > 3000:
            article_text = " ".join(words[:3000]) + "... [Teks dipotong karena terlalu panjang untuk limit API]"


        if not article_text.strip() or len(article_text.split()) < 30:
            # Dapatkan judul halaman untuk diagnosa pemblokiran
            page_title = parsing.title.string if parsing.title else "Tidak Ada Judul"
            word_count = len(article_text.split())
            raise ValueError(f"Scraping Gagal. Hanya ditemukan {word_count} kata. Judul halaman: '{page_title}'. Situs ini mungkin memblokir bot atau konten di-render via JavaScript.")
            
        return title, article_text, None
        
    except requests.exceptions.HTTPError as e:
        # Menunjukkan kode error seperti 403 (Forbidden) atau 429 (Too Many Requests)
        error_message = f"Website menolak akses. Status Code: {e.response.status_code} untuk URL: {e.request.url}"
        st.error(f"DEBUG: {error_message}")
        return "Gagal Ekstraksi", "", error_message
    except requests.exceptions.RequestException as e:
        # Menangkap semua error terkait koneksi/timeout
        error_message = f"Gagal terhubung ke URL. Error: {type(e).__name__} pada URL: {e.request.url}"
        st.error(f"DEBUG: {error_message}")
        return "Gagal Ekstraksi", "", error_message
    except Exception as e:
        # Menangkap error mungkin terjadi saat parsing
        error_message = f"Terjadi kesalahan saat scraping. Error: {type(e).__name__}. Detail: {str(e)}"
        st.error(f"DEBUG: {error_message}")
        return "Gagal Ekstraksi", "", error_message

# MODELING
@st.cache_data(ttl=3600, show_spinner="Menganalisis framing, aktor, sentimen, dan kata kunci...")
def comprehensive_analysis_with_llm(article_text, model_name):
    # Penanganan API Key Groq
    api_key = st.secrets.get("GROQ_API_KEY") or st.session_state.get("custom_groq_key")
    if not api_key: return {"error": "API Key Groq tidak ditemukan."}
    
    client = Groq(api_key=api_key)

    system_prompt = """
    Anda adalah seorang analis media yang ahli. Tugas Anda adalah menganalisis teks berita yang diberikan secara komprehensif.
    Lakukan tiga jenis analisis berikut:
    1. Analisis Framing (Robert Entman): Identifikasi 4 fungsi framing (Problem Definition, Causal Interpretation, Moral Evaluation, Treatment Recommendation).
    2. Analisis Aktor: Identifikasi 3-5 aktor utama.
    3. Analisis Sentimen: Tentukan sentimen (Positif, Negatif, atau Netral) dan alasan singkatnya.

    Jawab HANYA dalam format JSON yang valid.
    """

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": article_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"Groq SDK Error: {str(e)}"}


def run_full_analysis(url, model_name):
    # Analysis untuk satu URL berita dan deteksi bahasa berita
    title, text, error = scrape_article(url)
    lang = 'indonesian'
    if error:
        return ArticleAnalysis(url, title, text, None, f"Gagal mengekstrak konten. Penyebab: {error}", lang)
    
    try:
        lang_code = detect(text)
        if lang_code == 'id': lang = 'indonesian'
        elif lang_code == 'en': lang = 'english'
    except LangDetectException: pass

    analysis_results = comprehensive_analysis_with_llm(text, model_name)
    if "error" in analysis_results:
        return ArticleAnalysis(url, title, text, None, f"Gagal menganalisis konten. Penyebab: {analysis_results['error']}", lang)
        
    return ArticleAnalysis(url, title, text, analysis_results, None, lang)

# EVALUATION
def display_analysis_table(results):
    # HANYA menampilkan judul dan sumber (Header saja)
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if not valid_results: return

    cols_header = st.columns(len(valid_results))
    for i, res in enumerate(valid_results):
        with cols_header[i]:
            st.subheader(res.title)
            st.caption(f"Sumber: [{res.url.split('/')[2]}]({res.url})")


# EVALUATION


def display_actor_analysis(results):
    # Menampilkan perbandingan aktor utama
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if not valid_results: return
    
    st.header("🎭 Analisis Aktor", divider='gray')
    cols = st.columns(len(valid_results))
    for i, res in enumerate(valid_results):
        with cols[i]:
            st.subheader(f"Aktor di '{res.title}'")
            actors = res.analysis_results.get('actors', ['Tidak ditemukan'])
            st.markdown("- " + "\n- ".join(actors))

def display_sentiment_analysis(results):
    # Menampilkan perbandingan sentimen dengan alasannya
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if not valid_results: return
    
    st.header("🙂 Analisis Sentimen", divider='gray')
    cols = st.columns(len(valid_results))
    sentiment_map = {"Positif": "🙂 Positif", "Negatif": "☹️ Negatif", "Netral": "😐 Netral"}
    for i, res in enumerate(valid_results):
        with cols[i]:
            st.subheader(f"Sentimen di '{res.title}'")
            sentiment = res.analysis_results.get('sentiment', 'Tidak diketahui')
            reason = res.analysis_results.get('sentiment_reason', '')
            st.markdown(f"### {sentiment_map.get(sentiment, sentiment)}")
            if reason:
                st.caption(f"Alasan: {reason}")


@st.cache_data(ttl=3600, show_spinner="Membuat analisis komparatif...")
def generate_comparative_summary(results, model_name):
    # Membuat ringkasan analisis via Groq
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if len(valid_results) < 2: return "Analisis komparatif membutuhkan setidaknya dua artikel."

    api_key = st.secrets.get("GROQ_API_KEY") or st.session_state.get("custom_groq_key")
    if not api_key: return "API Key Groq tidak ditemukan."
    
    client = Groq(api_key=api_key)
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if not valid_results: return "Data tidak cukup untuk ringkasan."

    context = ""
    for res in valid_results:
        context += f"Judul: {res.title}\nFraming:\n"
        for key, value in res.analysis_results.get('framing', {}).items():
            context += f"{key}: {value}\n"
        context += "\n"

    user_prompt = f"Anda adalah seorang analis media senior. Buatlah laporan analisis komparatif formal (tanpa emoji) berdasarkan data berikut:\n{context}"

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Gagal membuat ringkasan: {str(e)}"

def extract_keywords(text, lang='indonesian', top_n=15):
    # Mengekstrak kata kunci berita menggunakan TF-IDF
    text = re.sub(r'\d+', '', text).lower()
    stop_words = list(nltk.corpus.stopwords.words(lang)) if lang in nltk.corpus.stopwords.fileids() else []
    custom_stopwords = ['yakni', 'yaitu', 'tersebut', 'kata', 'ujar', 'jelas', 'ungkap', 'menurut', 'antara', 'pihak', 'namun', 'sementara', 'saat', 'cnn', 'com', 'detik', 'kompas', 'said', 'also', 'would', 'could']
    stop_words.extend(custom_stopwords)
    try:
        vectorizer = TfidfVectorizer(max_features=top_n, stop_words=stop_words)
        vectorizer.fit_transform([text])
        return vectorizer.get_feature_names_out()
    except ValueError: return []

def create_keyword_graph(results):
    # Membuat graf kata kunci menggunakan NetworkX
    valid_results = [res for res in results if res.text and not res.error]
    if len(valid_results) < 2: return None

    keyword_sets = [set(extract_keywords(res.text, lang=res.lang)) for res in valid_results]
    all_keywords_flat = [kw for ks in keyword_sets for kw in ks]
    keyword_counts = Counter(all_keywords_flat)

    G = nx.Graph()
    source_nodes = [res.url.split('/')[2].replace('www.','').split('.')[0] for res in valid_results]
    G.add_nodes_from(source_nodes, type='source')

    for kw, count in keyword_counts.items():
        if count > 1:
            G.add_node(kw, type='common')
        else:
            owner_index = -1
            for i, ks in enumerate(keyword_sets):
                if kw in ks:
                    owner_index = i
                    break
            G.add_node(kw, type=f'unique_{owner_index}')

    for kw in G.nodes():
        if G.nodes[kw]['type'] != 'source':
            for i, ks in enumerate(keyword_sets):
                if kw in ks:
                    G.add_edge(source_nodes[i], kw)
            
    unique_colors = ['#EF553B', "#2A35D1", "#9E07FD"]
    color_map = []
    for node in G:
        node_type = G.nodes[node]['type']
        if node_type == 'source':
            color_map.append('orange')
        elif node_type == 'common':
            color_map.append('green')
        elif node_type.startswith('unique_'):
            idx = int(node_type.split('_')[-1])
            color_map.append(unique_colors[idx % len(unique_colors)])
            
    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
    
    fig, ax = plt.subplots(figsize=(20, 10))
    nx.draw(G, pos, with_labels=True, node_color=color_map, node_size=2500, font_size=11, font_color='white', width=0.8, edge_color='grey', ax=ax)
    
    ax.set_facecolor('#0E1117'); fig.set_facecolor('#0E1117'); plt.margins(0.05)
    return fig

# CSS UNTUK TAMPILAN PREMIUM
def apply_custom_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            background-color: #2A35D1;
            color: white;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #1E28A0;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(42, 53, 209, 0.3);
        }
        
        .landing-title {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #FFFFFF, #2A35D1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .theory-card {
            background-color: #1E1E1E;
            padding: 2rem;
            border-radius: 12px;
            border-left: 5px solid #2A35D1;
            margin: 1.5rem 0;
        }

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background-color: #0e1117 !important;
            border-right: 1px solid rgba(255,255,255,0.06) !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem !important;
        }
        /* Header App */
        .sidebar-header-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 2px;
        }
        .sidebar-title {
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            letter-spacing: -0.01rem !important;
            line-height: 1.15 !important;
            margin: 0 !important;
        }
        .sidebar-subtitle {
            font-size: 10px !important;
            font-weight: 400 !important;
            color: #666666 !important;
            letter-spacing: 0.06rem !important;
            line-height: 1.3 !important;
            margin-top: 4px !important;
            margin-bottom: 1.2rem !important;
            text-transform: uppercase !important;
        }
        /* Konfigurasi section header */
        .sidebar-section-header {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            color: #9CA3AF !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08rem !important;
            margin: 0 0 0.6rem 0 !important;
        }
        /* Nav Menu Items */
        [data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 2px;
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            padding: 10px 15px !important;
            border-radius: 8px !important;
            margin-bottom: 4px !important;
            transition: background 0.15s ease;
            cursor: pointer;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
            background-color: rgba(255,255,255,0.06) !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] [aria-checked="true"] {
            background-color: #1e2030 !important;
            border-left: 3px solid #2A35D1 !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label div:last-child {
            color: #e5e7eb !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }
        /* Override h2 inside sidebar */
        [data-testid="stSidebar"] h2 {
            display: none !important;
        }
        /* Selectbox label inside sidebar */
        [data-testid="stSidebar"] .stSelectbox label p {
            font-size: 0.78rem !important;
            color: #9CA3AF !important;
        }
        /* Caption / version text */
        [data-testid="stSidebar"] .stCaption {
            font-size: 0.7rem !important;
            color: #4B5563 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def display_landing_page():
    st.markdown('<h1 class="landing-title">📰 News Framing Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
        Aplikasi ini menggunakan Model **Llama 3.1 & 3.3 via Groq** untuk menganalisis dan membandingkan bagaimana berbagai media online 
        membingkai (**framing**) sebuah isu berdasarkan teori **Robert Entman (1993)**.
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
        *   **Identifikasi Framing Otomatis:** Bedah teks berita secara mendalam dalam hitungan detik.
        *   **Pemetaan Aktor Utama:** Deteksi tokoh, kelompok, atau lembaga yang paling berpengaruh.
        *   **Analisis Sentimen & Keyword:** Memahami nada pemberitaan dan kata kunci yang mendominasi narasi.
        *   **Graf Hubungan Media:** Visualisasi keterkaitan antar media berdasarkan kesamaan kata kunci.
    """)
    
    st.info("Kecepatan tinggi didukung oleh Llama 3 (via Groq) untuk efisiensi analisis data besar.")
    
    if st.button("Mulai Analisis Sekarang →"):
        st.session_state['current_page'] = 'Analysis'
        st.rerun()


# DEPLOYMENT (MAIN FUNCTION APLIKASI)

def display_framing_comparison(results):
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if not valid_results: return
    f_map = {
        "Definisi Masalah": "problem_definition",
        "Interpretasi Penyebab": "causal_interpretation",
        "Evaluasi Moral": "moral_evaluation",
        "Rekomendasi Solusi": "treatment_recommendation"
    }
    for label, key in f_map.items():
        st.markdown(f"#### {label}")
        cols = st.columns(len(valid_results))
        for i, res in enumerate(valid_results):
            with cols[i]:
                txt = res.analysis_results.get('framing', {}).get(key, 'N/A')
                if key == "problem_definition": st.info(txt)
                elif key == "causal_interpretation": st.warning(txt)
                elif key == "moral_evaluation": st.error(txt)
                elif key == "treatment_recommendation": st.success(txt)
    st.divider()

def main():
    apply_custom_style()
    
    # Inisialisasi session state navigasi
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'Home'
    if 'nav_key' not in st.session_state:
        st.session_state['nav_key'] = "🏠 Beranda"
    
    # Sidebar Navigasi
    with st.sidebar:
        # Layout Header Gabungan
        st.markdown("""
            <div class="sidebar-header-container">
                <span style="font-size: 2rem;">📰</span>
                <p class="sidebar-title">NEWS FRAMING<br>ANALYSIS</p>
            </div>
            <p class="sidebar-subtitle">AUTOMATED MEDIA ANALYSIS &<br>FRAMING INTELLIGENCE</p>
        """, unsafe_allow_html=True)
        
        nav_options = ["🏠 Beranda", "🔍 Analisis Framing"]
        nav_map = {"🏠 Beranda": "Home", "🔍 Analisis Framing": "Analysis"}
        
        # Callback untuk navigasi instan
        def handle_nav():
            st.session_state['current_page'] = nav_map[st.session_state.nav_key]

        st.radio(
            "Navigasi",
            options=nav_options,
            index=0 if st.session_state.get('current_page', 'Home') == 'Home' else 1,
            key="nav_key",
            on_change=handle_nav,
            label_visibility="collapsed"
        )

    if st.session_state.get('current_page', 'Home') == 'Home':
        display_landing_page()
        return

    # HALAMAN ANALISIS
    st.header("🔍 Analisis Framing")
    
    # Sidebar untuk Konfigurasi (di bawah navigasi)
    with st.sidebar:
        st.divider()
        st.markdown('<p class="sidebar-section-header">⚙️ Konfigurasi Model</p>', unsafe_allow_html=True)
        model_options = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"]
        model_option = st.selectbox("Model AI", model_options, index=0)
        st.session_state['selected_model'] = model_option
        st.divider()
        st.caption("News Framing Analysis v2.5")

    # Inisialisasi session state
    if 'urls_input' not in st.session_state: st.session_state['urls_input'] = ""
    
    tab_link, tab_manual = st.tabs(["🔗 Link Berita", "✍️ Teks Manual"])
    
    articles_to_analyze = [] # List of tuples (title, text, url)

    with tab_link:
        urls_input = st.text_area(
            "Masukkan 2-3 URL berita (satu per baris)", 
            height=120, 
            key="urls_input_area",
            placeholder="Contoh: https://news.detik.com/..."
        )
            
        if st.button("📝 Analisis dari Link", type="primary"):
            urls = [u.strip() for u in urls_input.split('\n') if u.strip()]
            if 2 <= len(urls) <= 3:
                with st.spinner("Mengekstrak berita dari link..."):
                    for url in urls:
                        title, text, error = scrape_article(url)
                        if not error:
                            articles_to_analyze.append((title, text, url))
                        else:
                            st.error(f"Gagal mengambil {url}: {error}")
            else:
                st.warning("Masukkan 2-3 link.")



    with tab_manual:
        st.info("Gunakan mode ini jika scraping otomatis gagal. Copy-paste isi berita langsung.")
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
                st.warning("Isi setidaknya dua berita.")

    # PIPELINE ANALISIS (Sama untuk semua input)
    if articles_to_analyze:
        if "GROQ_API_KEY" not in st.secrets:
            st.error("API Key Groq belum dikonfigurasi di backend (secrets.toml)."); st.stop()

            
        all_results = []
        progress_bar = st.progress(0, text="Menganalisis konten dengan AI...")
        
        for i, (title, text, url) in enumerate(articles_to_analyze):
            progress_bar.progress((i+1)/len(articles_to_analyze), text=f"Menganalisis: {title[:30]}...")
            
            # Deteksi bahasa
            lang = 'indonesian'
            try:
                lang_code = detect(text)
                if lang_code == 'en': lang = 'english'
            except: pass
            
            analysis = comprehensive_analysis_with_llm(text, model_option)
            if "error" in analysis:
                st.error(f"Error pada '{title}': {analysis['error']}")
            else:
                all_results.append(ArticleAnalysis(url, title, text, analysis, None, lang))
        
        progress_bar.empty()
        
        if len(all_results) >= 2:
            st.divider()
            st.header("📰 Artikel yang Dianalisis", divider='gray')
            display_analysis_table(all_results)
            
            # SISTEM TAB UNTUK HASIL ANALISIS
            tab_summary, tab_framing, tab_actors, tab_graph = st.tabs([
                "📈 Analisis Framing Komparatif", 
                "🏗️ Struktur Framing", 
                "👥 Aktor & Sentimen", 
                "🕸️ Graf Kata Kunci"
            ])

            
            with tab_summary:
                st.subheader("Analisis Framing Komparatif")
                summary = generate_comparative_summary(all_results, model_option)
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
                fig = create_keyword_graph(all_results)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("Data tidak cukup untuk membuat graf.")
        else:
            st.error("Minimal butuh 2 berita yang berhasil dianalisis.")

if __name__ == "__main__":
    main()
