import streamlit as st


def apply_custom_styles():
    """Apply modern UI/UX custom styles."""
    st.markdown("""
    <style>
    /* Modern font and spacing */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(49, 131, 207, 0.1);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Text area styling */
    .stTextArea textarea {
        border-radius: 8px;
        font-size: 0.9rem;
    }

    /* Slider styling */
    .stSlider > div > div {
        padding-top: 0.5rem;
    }

    /* Container borders */
    [data-testid="stVerticalBlock"] > div:has(> [data-testid="stContainer"]) {
        border-radius: 12px;
    }

    /* Info/success/warning boxes */
    .stAlert {
        border-radius: 8px;
    }

    /* Code blocks */
    .stCodeBlock {
        border-radius: 8px;
    }

    /* Responsive: stack columns on smaller screens */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: rgba(49, 131, 207, 0.05);
        border-radius: 8px;
        padding: 1rem;
    }

    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
