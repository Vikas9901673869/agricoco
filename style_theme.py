import streamlit as st
import streamlit.components.v1 as components

def apply_palm_theme(badge_text="PRECISION AG-TECH AI SUITE", title_text="PalmGuard Agronomy Cloud", sub_text="Real-time edge diagnostics for coconut & palm ecosystems."):
    """Injects the global enterprise CSS, background coconut trees, and hero header."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Dual Coconut Tree Silhouettes Background */
    .stApp {
        background-color: #f8fafc !important;
        background-image: 
            radial-gradient(circle at 85% 15%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 15% 85%, rgba(5, 150, 105, 0.06) 0%, transparent 60%),
            /* Left Palm Tree */
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 300' fill='%23059669' opacity='0.05'%3E%3Cpath d='M100 280 C95 200 70 120 100 60 C80 50 40 55 20 70 C40 85 70 85 85 95 C60 105 30 120 15 145 C35 150 70 140 85 130 C65 145 45 175 35 205 C55 195 80 175 90 155 C90 200 95 240 100 280 Z'/%3E%3Cpath d='M100 60 C115 45 155 45 180 55 C160 70 130 75 115 85 C140 90 175 105 190 130 C170 135 135 130 115 120 C135 135 160 160 170 190 C150 180 125 165 110 145'/%3E%3C/svg%3E"),
            /* Right Palm Tree */
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 240 340' fill='%23047857' opacity='0.06'%3E%3Cpath d='M140 330 C135 230 110 130 130 60 C110 50 60 50 30 70 C55 85 95 85 110 100 C80 110 40 130 20 160 C50 165 90 150 110 135 C85 155 60 190 50 225 C75 210 105 190 120 165 C120 220 130 275 140 330 Z'/%3E%3Cpath d='M130 60 C150 40 195 40 225 50 C200 70 165 75 145 90 C175 95 215 110 235 140 C210 145 170 140 145 125 C170 145 200 175 215 210 C190 195 155 175 138 155'/%3E%3C/svg%3E") !important;
        background-position: top right, bottom left, left -20px bottom 0px, right -30px bottom 0px !important;
        background-size: auto, auto, 280px 420px, 340px 480px !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }

    /* Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, rgba(13, 59, 46, 0.95) 0%, rgba(23, 84, 56, 0.92) 50%, rgba(15, 46, 34, 0.95) 100%);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        color: #ffffff;
        box-shadow: 0 20px 40px -15px rgba(13, 59, 46, 0.35);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #a7f3d0;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 10px 0;
        background: linear-gradient(to right, #ffffff, #d1fae5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: #a7f3d0;
        margin: 0;
        line-height: 1.5;
    }

    /* Modern Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        transition: all 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 28px rgba(16, 185, 129, 0.12);
        border-color: #10b981;
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #10b981;
        font-weight: 600;
    }

    /* Glass Panels */
    .glass-panel {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(12px);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1.8rem;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.8rem;
    }
    .panel-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 1rem;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 0.75rem;
    }

    /* Button Enhancements */
    .stButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 0.65rem 1.4rem !important;
        border: none !important;
    }

    /* Sidebar Theme */
    [data-testid="stSidebar"] {
        background-color: #09261d !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Render Hero Card
    st.markdown(f"""
    <div class="hero-container">
        <span class="hero-badge">{badge_text}</span>
        <h1 class="hero-title">{title_text}</h1>
        <p class="hero-sub">{sub_text}</p>
    </div>
    """, unsafe_allow_html=True)

    # Scrub Deploy Banner
    components.html("""
    <script>
    function cleanUI() {
        const doc = window.parent.document;
        doc.querySelectorAll('button').forEach(b => {
            if ((b.innerText||"").trim().toLowerCase() === 'deploy') b.remove();
        });
        doc.querySelectorAll('footer').forEach(f => f.style.display = 'none');
    }
    cleanUI(); setInterval(cleanUI, 500);
    </script>
    """, height=0, width=0)