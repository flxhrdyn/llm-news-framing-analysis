import re
from collections import Counter

import nltk
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import CUSTOM_STOPWORDS


def extract_keywords(text: str, lang: str = "indonesian", top_n: int = 15) -> list[str]:
    """Mengekstrak kata kunci paling signifikan dari sebuah teks menggunakan TF-IDF.

    Angka-angka dihapus terlebih dahulu karena biasanya tidak berkontribusi
    pada makna tematik artikel. Stopwords dari NLTK dikombinasikan dengan
    daftar stopwords kustom khusus konten berita untuk hasil yang lebih bersih.

    Args:
        text: Teks artikel yang akan diproses.
        lang: Bahasa teks, digunakan untuk memilih stopwords NLTK yang tepat.
              Nilai yang didukung adalah 'indonesian' dan 'english'.
        top_n: Jumlah maksimal kata kunci yang dikembalikan.

    Returns:
        List berisi kata kunci yang paling signifikan dalam teks,
        atau list kosong jika teks terlalu pendek untuk diproses.
    """
    text = re.sub(r"\d+", "", text).lower()

    if lang in nltk.corpus.stopwords.fileids():
        stop_words = list(nltk.corpus.stopwords.words(lang))
    else:
        stop_words = []

    stop_words.extend(CUSTOM_STOPWORDS)

    try:
        # Gunakan TfidfVectorizer sementara untuk memproses stopwords agar konsisten
        temp_vec = TfidfVectorizer()
        analyze = temp_vec.build_analyzer()
        fixed_stop_words = list(set([word for sw in stop_words for word in analyze(sw)]))
        
        vectorizer = TfidfVectorizer(max_features=top_n, stop_words=fixed_stop_words)
        vectorizer.fit_transform([text])
        return list(vectorizer.get_feature_names_out())
    except ValueError:
        return []


def build_keyword_graph(results: list) -> plt.Figure | None:
    """Membangun graf kata kunci yang menunjukkan hubungan antar media berdasarkan kata kunci bersama.

    Setiap node dalam graf mewakili sebuah sumber media atau sebuah kata kunci.
    Kata kunci yang muncul di lebih dari satu media diberi warna hijau (kata kunci bersama),
    sedangkan kata kunci unik milik satu media diberi warna yang berbeda untuk setiap sumber.

    Args:
        results: List berisi objek ArticleAnalysis yang sudah memiliki teks artikel.

    Returns:
        Objek Figure dari Matplotlib yang berisi visualisasi graf,
        atau None jika data tidak cukup untuk membuat graf yang bermakna.
    """
    valid_results = [r for r in results if r.text and not r.error]
    if len(valid_results) < 2:
        return None

    keyword_sets = [set(extract_keywords(r.text, lang=r.lang)) for r in valid_results]
    all_keywords = [kw for ks in keyword_sets for kw in ks]
    keyword_counts = Counter(all_keywords)

    graph = nx.Graph()

    # Tambahkan node sumber media menggunakan nama domain yang lebih lengkap
    source_nodes = []
    for r in valid_results:
        domain = r.url.split("/")[2].replace("www.", "")
        # Ambil dua bagian pertama jika ada subdomain (misal: news.detik.com -> news.detik)
        parts = domain.split(".")
        name = ".".join(parts[:-1]) if len(parts) > 1 else parts[0]
        source_nodes.append(name)
        
    graph.add_nodes_from(source_nodes, node_type="source")

    # Tambahkan node kata kunci dan tentukan tipenya berdasarkan kemunculannya
    for kw, count in keyword_counts.items():
        if count > 1:
            graph.add_node(kw, node_type="common")
        else:
            owner_index = next(
                (i for i, ks in enumerate(keyword_sets) if kw in ks), -1
            )
            graph.add_node(kw, node_type=f"unique_{owner_index}")

    # Hubungkan setiap kata kunci ke sumber medianya dengan edge
    for kw in list(graph.nodes()):
        if graph.nodes[kw]["node_type"] == "source":
            continue
        for i, ks in enumerate(keyword_sets):
            if kw in ks:
                graph.add_edge(source_nodes[i], kw)

    color_map = _build_color_map(graph, source_nodes)

    pos = nx.spring_layout(graph, k=0.8, iterations=50, seed=42)
    fig, ax = plt.subplots(figsize=(20, 10))

    nx.draw(
        graph, pos,
        with_labels=True,
        node_color=color_map,
        node_size=2500,
        font_size=11,
        font_color="white",
        width=0.8,
        edge_color="grey",
        ax=ax,
    )

    # Tambahkan Legenda
    from matplotlib.lines import Line2D
    unique_colors = ["#EF553B", "#2A35D1", "#9E07FD"]
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Sumber Media', markerfacecolor='orange', markersize=15),
        Line2D([0], [0], marker='o', color='w', label='Kata Kunci Bersama', markerfacecolor='green', markersize=15),
    ]
    for i, name in enumerate(source_nodes):
        legend_elements.append(
            Line2D([0], [0], marker='o', color='w', label=f'Unik: {name}', 
                   markerfacecolor=unique_colors[i % len(unique_colors)], markersize=15)
        )
    
    ax.legend(handles=legend_elements, loc='upper right', frameon=True, 
              facecolor='#1E1E1E', labelcolor='white', fontsize=10)

    ax.set_facecolor("#0E1117")
    fig.set_facecolor("#0E1117")
    plt.margins(0.05)

    return fig


def _build_color_map(graph: nx.Graph, source_nodes: list[str]) -> list[str]:
    """Menentukan warna setiap node dalam graf berdasarkan tipenya.

    Node sumber media berwarna oranye, kata kunci bersama berwarna hijau,
    dan kata kunci unik mendapatkan warna yang berbeda per sumber.
    """
    unique_colors = ["#EF553B", "#2A35D1", "#9E07FD"]
    color_map = []

    for node in graph.nodes():
        node_type = graph.nodes[node]["node_type"]
        if node_type == "source":
            color_map.append("orange")
        elif node_type == "common":
            color_map.append("green")
        else:
            idx = int(node_type.split("_")[-1])
            color_map.append(unique_colors[idx % len(unique_colors)])

    return color_map
