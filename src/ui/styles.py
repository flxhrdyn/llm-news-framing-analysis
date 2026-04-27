import streamlit as st


def apply_custom_style():
    """Menyuntikkan CSS kustom ke dalam aplikasi Streamlit.

    CSS ini mendefinisikan keseluruhan design system aplikasi, termasuk
    tipografi dengan font Inter, skema warna biru gelap premium, gaya
    komponen sidebar, dan efek interaktif pada tombol dan menu navigasi.
    Pendekatan sentralisasi CSS di sini memudahkan perubahan tema secara menyeluruh
    tanpa harus menyentuh kode tampilan di banyak tempat.
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            background-color: #2A35D1;
            color: white;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
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

        /* Sidebar utama */
        [data-testid="stSidebar"] {
            background-color: #0e1117 !important;
            border-right: 1px solid rgba(255,255,255,0.06) !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem !important;
        }

        /* Header aplikasi di dalam sidebar */
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

        /* Label bagian konfigurasi di sidebar */
        .sidebar-section-header {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            color: #9CA3AF !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08rem !important;
            margin: 0 0 0.6rem 0 !important;
        }

        /* Menu navigasi radio button yang dimodifikasi menjadi list menu */
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

        /* Sembunyikan heading h2 bawaan Streamlit di dalam sidebar */
        [data-testid="stSidebar"] h2 {
            display: none !important;
        }

        /* Label selectbox di dalam sidebar */
        [data-testid="stSidebar"] .stSelectbox label p {
            font-size: 0.78rem !important;
            color: #9CA3AF !important;
        }

        /* Teks caption versi aplikasi */
        [data-testid="stSidebar"] .stCaption {
            font-size: 0.7rem !important;
            color: #4B5563 !important;
        }
        </style>
    """, unsafe_allow_html=True)
