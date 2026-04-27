import streamlit as st

from src.config import AVAILABLE_MODELS


def render_sidebar() -> tuple[str, str]:
    """Merender seluruh konten sidebar, termasuk header aplikasi, navigasi, dan konfigurasi model.

    Navigasi menggunakan st.radio yang telah dimodifikasi tampilannya via CSS
    agar tampak seperti menu list modern tanpa lingkaran radio. Perubahan
    navigasi langsung memperbarui session state melalui callback sehingga
    perpindahan halaman terjadi secara instan hanya dengan satu klik.

    Returns:
        Tuple berisi (nama_halaman_aktif, nama_model_terpilih).
        Nama halaman aktif adalah salah satu dari 'Home' atau 'Analysis'.
    """
    with st.sidebar:
        st.markdown("""
            <div class="sidebar-header-container">
                <span style="font-size: 2rem;">📰</span>
                <p class="sidebar-title">NEWS FRAMING<br>ANALYSIS</p>
            </div>
            <p class="sidebar-subtitle">AUTOMATED MEDIA ANALYSIS &<br>FRAMING INTELLIGENCE</p>
        """, unsafe_allow_html=True)

        nav_options = ["🏠 Beranda", "🔍 Analisis Framing"]
        nav_map = {"🏠 Beranda": "Home", "🔍 Analisis Framing": "Analysis"}

        def on_nav_change():
            if "nav_key" in st.session_state:
                st.session_state["current_page"] = nav_map[st.session_state["nav_key"]]

        current_index = 0 if st.session_state.get("current_page", "Home") == "Home" else 1

        st.radio(
            "Navigasi Halaman",
            options=nav_options,
            index=current_index,
            key="nav_key",
            on_change=on_nav_change,
            label_visibility="collapsed",
        )

        # Bagian konfigurasi model hanya ditampilkan di halaman analisis
        selected_model = st.session_state.get("selected_model", AVAILABLE_MODELS[0])
        if st.session_state.get("current_page", "Home") == "Analysis":
            st.divider()
            st.markdown('<p class="sidebar-section-header">⚙️ Konfigurasi Model</p>', unsafe_allow_html=True)
            selected_model = st.selectbox("Model AI", AVAILABLE_MODELS, index=0)
            st.session_state["selected_model"] = selected_model
            st.divider()
            st.caption("News Framing Analysis v2.5")

    return st.session_state.get("current_page", "Home"), selected_model
