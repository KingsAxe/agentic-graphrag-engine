import streamlit as st

def apply_theme(demo_mode: bool = True):
    """
    World-Class 'Stripe Corporate' Light Mode UI styling.
    demo_mode=True increases font sizes for screen recordings.
    """

    # Font sizing 
    base_font = 16 if demo_mode else 15
    header_font = 36 if demo_mode else 30
    subheader_font = 24 if demo_mode else 20

    st.markdown(
        f"""
        <style>
        /* =========================
           GLOBAL TYPOGRAPHY (Inter)
        ========================== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"], [class*="st-"] {{
            font-family: 'Inter', sans-serif !important;
            font-size: {base_font}px !important;
            color: #1A1F36 !important;
        }}

        h1 {{
            font-size: {header_font}px !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
            color: #1A1F36 !important;
            margin-bottom: 2rem !important;
        }}

        h2, h3, h4, h5 {{
            font-size: {subheader_font}px !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            color: #1A1F36 !important;
        }}

        /* =========================
           APP BACKGROUND & CANVAS
        ========================== */
        .stApp {{
            background-color: #F6F9FC !important;
            color: #1A1F36 !important;
        }}

        /* Hide Top Header Line */
        header[data-testid="stHeader"] {{
            background: transparent !important;
            backdrop-filter: blur(12px) !important;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
        }}

        /* =========================
           INPUTS & TEXTAREAS
        ========================== */
        textarea, input {{
            background-color: #FFFFFF !important;
            color: #1A1F36 !important;
            border: 1px solid #E3E8EE !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}

        textarea:focus, input:focus {{
            border-color: #635BFF !important;
            box-shadow: 0 0 0 3px rgba(99, 91, 255, 0.15) !important;
            outline: none !important;
        }}

        /* Selectbox wrapper */
        div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border-radius: 8px !important;
            border: 1px solid #E3E8EE !important;
            color: #1A1F36 !important;
        }}
        /* Fix text color inside dropdown */
        div[data-baseweb="select"] * {{
            color: #1A1F36 !important;
        }}

        /* =========================
           BUTTONS (PRIMARY ACCENT)
        ========================== */
        .stButton > button {{
            border-radius: 8px !important;
            padding: 0.75rem 1.75rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
            background: #635BFF !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 14px 0 rgba(99, 91, 255, 0.3) !important;
            transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 91, 255, 0.4) !important;
            background: #7A73FF !important;
        }}

        .stButton > button:disabled {{
            background: #E3E8EE !important;
            box-shadow: none !important;
            color: #A3ACBA !important;
            cursor: not-allowed !important;
            transform: none !important;
        }}

        /* =========================
           CARDS / CONTAINERS (CLEAN WHITE)
        ========================== */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: #FFFFFF !important;
            border: 1px solid #E3E8EE !important;
            border-radius: 12px !important;
            padding: 24px !important;
            box-shadow: 0 4px 6px -1px rgba(50, 50, 93, 0.05), 0 1px 3px -1px rgba(0, 0, 0, 0.05) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            box-shadow: 0 13px 27px -5px rgba(50, 50, 93, 0.1), 0 8px 16px -8px rgba(0, 0, 0, 0.1) !important;
            transform: translateY(-1px) !important;
        }}

        /* =========================
           METRICS
        ========================== */
        div[data-testid="stMetric"] {{
            background: #FFFFFF !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            border: 1px solid #E3E8EE !important;
            box-shadow: 0 2px 5px -1px rgba(50, 50, 93, 0.05), 0 1px 3px -1px rgba(0, 0, 0, 0.05) !important;
        }}
        
        div[data-testid="stMetricValue"] {{
            font-weight: 800 !important;
            color: #1A1F36 !important;
        }}
        
        div[data-testid="stMetricLabel"] {{
            font-weight: 500 !important;
            color: #4F566B !important;
        }}

        /* =========================
           CODE BLOCKS
        ========================== */
        pre {{
            background-color: #F7F9FC !important;
            border-radius: 8px !important;
            border: 1px solid #E3E8EE !important;
            padding: 1rem !important;
        }}
        pre code {{
            color: #1A1F36 !important; 
        }}

        /* =========================
           EXPANDERS
        ========================== */
        details {{
            background: #FFFFFF !important;
            border-radius: 8px !important;
            border: 1px solid #E3E8EE !important;
            padding: 12px 16px !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
        }}

        summary {{
            font-weight: 600 !important;
            color: #1A1F36 !important;
        }}

        /* =========================
           SIDEBAR
        ========================== */
        section[data-testid="stSidebar"] {{
            background-color: #F6F9FC !important;
            border-right: 1px solid #E3E8EE !important;
        }}

        /* =========================
           CAPTIONS & DIVIDERS
        ========================== */
        .stCaption {{
            color: #4F566B !important;
            font-weight: 500 !important;
        }}
        
        hr [data-testid="stMarkdownContainer"] {{
            border-color: #E3E8EE !important;
        }}

        /* =========================
           HERO COMPONENT
        ========================== */
        .sre-hero {{
            background: #FFFFFF;
            border: 1px solid #E3E8EE;
            border-left: 4px solid #635BFF;
            border-radius: 12px;
            padding: 24px;
            margin: 0px 0 32px 0;
            box-shadow: 0 7px 14px 0 rgba(60, 66, 87, 0.08), 0 3px 6px 0 rgba(0, 0, 0, 0.08);
            position: relative;
            overflow: hidden;
        }}
        
        /* Subtle colored gradient wash in the corner */
        .sre-hero::before {{
            content: "";
            position: absolute;
            top: -100px;
            right: -100px;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(99, 91, 255, 0.08) 0%, rgba(255, 255, 255, 0) 70%);
            border-radius: 50%;
            z-index: 0;
            pointer-events: none;
        }}

        .sre-hero-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            position: relative;
            z-index: 1;
        }}

        .sre-hero-title {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #1A1F36;
        }}

        .sre-hero-subtitle {{
            margin-top: 8px;
            font-size: 16px;
            color: #4F566B;
            line-height: 1.6;
            font-weight: 500;
            position: relative;
            z-index: 1;
        }}

        .sre-hero-badge {{
            background: #F2F5FA;
            border: 1px solid #E3E8EE;
            padding: 6px 12px;
            border-radius: 999px;
            color: #635BFF;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 800;
        }}

        /* =========================
           LEFT NAV (SIDEBAR CUSTOM TABS)
        ========================== */
        .sre-side-title {{
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #1A1F36;
        }}

        .sre-side-sub {{
            margin-top: 4px;
            color: #4F566B;
            font-size: 13px;
            font-weight: 500;
        }}

        .sre-nav-item {{
            padding: 10px 14px;
            border-radius: 6px;
            margin: 6px 0;
            background: transparent;
            border: 1px solid transparent;
            color: #4F566B;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .sre-nav-item:hover {{
            background: rgba(85, 105, 135, 0.05);
            color: #1A1F36;
        }}

        .sre-nav-item.active {{
            background: #FFFFFF;
            border: 1px solid #E3E8EE;
            color: #635BFF;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

