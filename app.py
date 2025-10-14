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
def display_ui_header():
    # judul dan deskripsi aplikasi
    st.title("📰 News Framing Analysis")
    st.markdown("""
        Aplikasi ini menggunakan Model [**Gemini 2.5 Flash**](https://deepmind.google/models/gemini/flash/) untuk menganalisis dan membandingkan bagaimana beberapa media online **membingkai (framing)** sebuah isu, berdasarkan teori Robert Entman (1993), yaitu:
        - **Definisi Masalah (Problem Definition):** Apa yang dianggap sebagai masalah utama?
        - **Penyebab Masalah (Causal Interpretation):** Siapa atau apa yang dianggap sebagai penyebabnya?
        - **Penilaian Moral (Moral Evaluation):** Siapa 'pahlawan' dan 'penjahat' dalam narasi ini?
        - **Rekomendasi Solusi (Treatment Recommendation):** Apa solusi yang ditawarkan atau diimplikasikan?
        
        Sumber: [Entman, R.M., 1993. Framing: Towards clarification of a fractured paradigm. McQuail's reader in mass communication theory, 390, p.397.](https://fbaum.unc.edu/teaching/articles/J-Communication-1993-Entman.pdf)        

        Input URL artikel berita tentang topik yang sama dan model akan mengidentifikasi Framing, Aktor utama, Sentimen, serta Keyword berita secara otomatis. 
        Hasilnya akan disajikan dalam beberapa bagian analisis komparatif.
    """)

# DATA COLLECTION & PREPARATION
@st.cache_data(ttl=3600, show_spinner="Mengekstrak teks dari URL...")
def scrape_article(url):
    # Mengambil judul dan teks artikel dari URL
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'
        }

        response = requests.get(url.strip(), headers=headers, timeout=20)
        response.raise_for_status()
        
        content = response.content
        parsing = bs(content, 'lxml')
        
        title_tag = parsing.find(['h1', 'post-title', 'entry-title'])
        title = title_tag.get_text(strip=True) if title_tag else "Judul Tidak Ditemukan"
        
        selectors = [
            'article', 'div[class*="article-body"]', 'div[class*="post-content"]',
            'div[class*="main-content"]', 'div[class*="story-body"]', 'div[class*="rich-text-article-body"]',
            'div[id*="article-body"]',
        ]
        
        article_container = next((parsing.select_one(s) for s in selectors if parsing.select_one(s)), None)
        search_area = article_container if article_container else parsing
        
        paragraphs = search_area.find_all('p')
        article_text = " ".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True).split()) > 10])
        
        if article_container and (not article_text.strip() or len(article_text.split()) < 50):
              paragraphs = parsing.find_all('p')
              article_text = " ".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True).split()) > 10])

        if not article_text.strip() or len(article_text.split()) < 50:
            raise ValueError("Teks artikel tidak sesuai atau tidak dapat ditemukan.")
            
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
def comprehensive_analysis_with_llm(article_text):
    # Mengirim teks artikel ke Gemini API
    api_key = st.secrets["GEMINI_API_KEY"]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    system_prompt = """
    Anda adalah seorang analis media yang ahli. Tugas Anda adalah menganalisis teks berita yang diberikan secara komprehensif.
    Lakukan tiga jenis analisis berikut:
    1.  **Analisis Framing (Robert Entman)**: Identifikasi 4 fungsi framing (Problem Definition, Causal Interpretation, Moral Evaluation, Treatment Recommendation).
    2.  **Analisis Aktor**: Identifikasi 3-5 aktor utama (orang, kelompok, atau lembaga) yang paling berpengaruh dalam berita.
    3.  **Analisis Sentimen**: Tentukan sentimen keseluruhan (Positif, Negatif, atau Netral) dan berikan alasan singkat (satu kalimat) untuk sentimen tersebut.

    Jawab HANYA dalam format JSON yang valid dan lengkap dengan struktur seperti ini:
    {
        "framing": {
            "problem_definition": "...",
            "causal_interpretation": "...",
            "moral_evaluation": "...",
            "treatment_recommendation": "..."
        },
        "actors": ["Aktor 1", "Aktor 2", "Aktor 3"],
        "sentiment": "Positif",
        "sentiment_reason": "Alasan singkat mengapa sentimennya positif..."
    }
    PENTING: Seluruh nilai (value) dalam JSON harus dalam Bahasa Indonesia.
    """

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": article_text}]}]
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
            response.raise_for_status()
            
            result_json = response.json()
            raw_text = result_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '{}')
            cleaned_json_str = re.sub(r'```json\n|\n```', '', raw_text).strip()
            return json.loads(cleaned_json_str)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [503, 504, 500] and attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                return {"error": f"Gemini API Error: {e}"}
        except requests.exceptions.ReadTimeout as e:
            return {"error": f"Server timeout. Coba lagi dalam beberapa saat. Detail: {e}"}
        except Exception as e:
            return {"error": f"Terjadi kesalahan: {e}"}
            
    return {"error": "Gagal menghubungi server setelah beberapa kali percobaan."}


def run_full_analysis(url):
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

    analysis_results = comprehensive_analysis_with_llm(text)
    if "error" in analysis_results:
        return ArticleAnalysis(url, title, text, None, f"Gagal menganalisis konten. Penyebab: {analysis_results['error']}", lang)
        
    return ArticleAnalysis(url, title, text, analysis_results, None, lang)

# EVALUATION
def display_analysis_table(results):
    # Menampilkan tabel perbandingan hasil analisis framing
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if not valid_results: return

    st.header("📊 Tabel Perbandingan Framing", divider='gray')
    
    cols_header = st.columns(len(valid_results))
    for i, res in enumerate(valid_results):
        with cols_header[i]:
            st.subheader(res.title)
            st.caption(f"Sumber: [{res.url.split('/')[2]}]({res.url})")
            st.divider()

    framing_map = {
        "Definisi Masalah": "problem_definition",
        "Interpretasi Penyebab": "causal_interpretation",
        "Evaluasi Moral": "moral_evaluation",
        "Rekomendasi Solusi": "treatment_recommendation"
    }
    
    for label, key in framing_map.items():
        st.markdown(f"#### {label}")
        cols_content = st.columns(len(valid_results))
        for i, res in enumerate(valid_results):
            with cols_content[i]:
                framing = res.analysis_results.get('framing', {})
                text = framing.get(key, 'N/A')
                if key == "problem_definition": st.info(text)
                elif key == "causal_interpretation": st.warning(text)
                elif key == "moral_evaluation": st.error(text)
                elif key == "treatment_recommendation": st.success(text)
    st.divider()

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
def generate_comparative_summary(results):
    # Membuat ringkasan analisis dengan Gemini
    valid_results = [res for res in results if res.analysis_results and not res.error]
    if len(valid_results) < 2: return "Analisis komparatif membutuhkan setidaknya dua artikel yang berhasil diproses."

    context = ""
    for i, res in enumerate(valid_results):
        context += f"--- Analisis Artikel {i+1} ---\nSumber: {res.url.split('/')[2]}\n"
        framing = res.analysis_results.get('framing', {})
        for key, value in framing.items():
            context += f"{key}: {value}\n"
        context += "\n"

    api_key = st.secrets["GEMINI_API_KEY"]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    summary_points = "\n".join([f"* **Sumber {res.url.split('/')[2]}:** [Kesimpulan spesifik.]" for res in valid_results])
    user_prompt = f"""
    Anda adalah seorang analis media. Berdasarkan data framing berikut, buatlah analisis komparatif dalam Bahasa Indonesia tanpa kalimat pembuka.
    Gunakan format markdown ketat ini:
    **1. Persamaan Framing (Common Ground):**
    * [Poin 1 persamaan kunci...]
    **2. Perbedaan Framing (Contrasting Points):**
    * [Poin 1 perbedaan mencolok...]
    **3. Kesimpulan Framing Akhir per Media:**
    [Satu kalimat pengantar singkat.]
    {summary_points}
    Data analisis:
    {context}
    """
    payload = {"contents": [{"parts": [{"text": user_prompt}]}]}
    try:
        response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Gagal menghasilkan ringkasan komparatif: {e}"

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

# DEPLOYMENT (MAIN FUNCTION APLIKASI)
def main():
    display_ui_header()
    
    urls_input = st.text_area("👇 Input 2 atau 3 URL di sini (satu per baris)", height=100, placeholder="Contoh:\nhttps://www.kompas.com/berita-terkini/contoh-isu-x\nhttps://www.detik.com/news/contoh-isu-x")
    
    if st.button("📝 Analisis Sekarang!", type="primary", use_container_width=True):
        if "GEMINI_API_KEY" not in st.secrets or not st.secrets["GEMINI_API_KEY"]:
            st.error("API Key Gemini belum disetting pada file .streamlit/secrets.toml")
            st.stop()

        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        if not 2 <= len(urls) <= 3:
            st.warning("Mohon input antara 2 hingga 3 URL saja"); return

        all_results = []
        progress_bar = st.progress(0, text="Memulai proses analisis...")
        
        for i, url in enumerate(urls):
            progress_text = f"Memproses URL {i+1}/{len(urls)}: {url[:50]}..."
            progress_bar.progress((i + 1) / len(urls), text=progress_text)
            all_results.append(run_full_analysis(url))
        
        progress_bar.empty()

        success_count = sum(1 for res in all_results if not res.error)
        
        if success_count == len(urls):
            st.success("🎉 Seluruh artikel telah berhasil diproses!")
        elif success_count > 0:
            st.warning(f"Berhasil memproses {success_count} dari {len(urls)} artikel. Beberapa URL gagal.")
            for res in all_results:
                if res.error:
                    st.error(f"**URL Gagal:** {res.url}\n\n**Penyebab:** {res.error}")
        
        if success_count > 0:
            display_analysis_table(all_results)
            st.header("✍️ Analisis Framing Komparatif", divider='gray')
            summary = generate_comparative_summary(all_results)
            st.markdown(summary)
            display_actor_analysis(all_results)
            display_sentiment_analysis(all_results)
            st.header("🔑 Graf Kata Kunci", divider='gray')
            st.markdown("Graf ini menunjukkan **kata kunci utama** dan hubungannya. <span style='color:gold;'>●</span> Berita, <span style='color:green;'>●</span> Kata Kunci Bersama. Kata Kunci Unik diberi warna berbeda (<span style='color:#EF553B;'>●</span>, <span style='color:#2A35D1;'>●</span>, <span style='color:#9E07FD;'>●</span>) untuk setiap berita.", unsafe_allow_html=True)
            keyword_graph_fig = create_keyword_graph(all_results)
            if keyword_graph_fig:
                st.pyplot(keyword_graph_fig)
        else:
            st.error("Semua URL gagal diproses. Tidak ada analisis yang dapat ditampilkan. Silakan periksa URL dan coba lagi.")

if __name__ == "__main__":
    main()
