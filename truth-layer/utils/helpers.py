"""
Helpers — CSS injection and utility functions for Fact-Check AI.
"""

import streamlit as st


def get_status_emoji(status: str) -> str:
    return {"VERIFIED": "✅", "INACCURATE": "⚠️", "FALSE": "❌"}.get(status, "❓")


def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

    :root {
        --bg:       #080c14;
        --card:     #0f1623;
        --surface:  #161f2e;
        --green:    #00d4aa;
        --red:      #ff6b6b;
        --amber:    #ffd93d;
        --blue:     #6bcbff;
        --purple:   #c084fc;
        --text:     #e2e8f0;
        --muted:    #64748b;
        --border:   rgba(255,255,255,0.07);
    }

    /* ── Reset ─────────────────────────────────────── */
    .stApp { background: var(--bg); color: var(--text); }
    body, .stMarkdown { font-family: 'Syne', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem; max-width: 1300px; }
    section[data-testid="stSidebar"] { display: none; }

    /* ── Main header ────────────────────────────────── */
    .main-header { text-align: center; padding: 2rem 0 1rem; }
    .main-header h1 {
        font-size: 2.8rem; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(135deg, var(--green) 0%, var(--blue) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .header-subtitle { color: var(--muted); font-size: 0.9rem; font-family: 'Space Mono', monospace; margin-top: 0.4rem; }

    /* ── Step indicator ─────────────────────────────── */
    .step-active, .step-done, .step-pending {
        text-align: center;
        padding: 0.65rem 0.5rem;
        border-radius: 10px;
        font-family: 'Syne', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1.4;
        transition: all 0.2s;
    }
    .step-active {
        background: linear-gradient(135deg, rgba(0,212,170,0.18), rgba(107,203,255,0.12));
        border: 1.5px solid var(--green);
        color: var(--green);
    }
    .step-done {
        background: rgba(0,212,170,0.07);
        border: 1.5px solid rgba(0,212,170,0.3);
        color: rgba(0,212,170,0.7);
    }
    .step-pending {
        background: var(--card);
        border: 1.5px solid var(--border);
        color: var(--muted);
    }
    .step-active small, .step-done small, .step-pending small {
        display: block; font-size: 0.72rem; font-weight: 400;
        opacity: 0.75; font-family: 'Space Mono', monospace;
    }
    .step-divider { height: 2px; background: var(--border); margin: 1rem 0 1.8rem; border-radius: 2px; }

    /* ── File card ──────────────────────────────────── */
    .file-card {
        display: flex; align-items: center; gap: 14px;
        background: var(--card); border: 1px solid var(--green);
        border-radius: 10px; padding: 14px 18px; margin: 12px 0;
    }
    .file-icon { font-size: 2rem; }

    /* ── Evidence card ──────────────────────────────── */
    /* correction box */
    .correction-box {
        background: rgba(255,107,107,0.08);
        border-left: 3px solid #ff6b6b;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px; margin: 10px 0;
        font-size: 0.9rem; line-height: 1.5;
    }
    .correction-label {
        font-weight: 700; color: #ff6b6b;
        display: block; margin-bottom: 4px;
        font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;
    }

    .evidence-card {
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 8px; padding: 10px 14px; margin: 5px 0; font-size: 0.84rem;
    }
    .evidence-card a { color: var(--blue); text-decoration: none; }
    .evidence-card a:hover { text-decoration: underline; }

    /* ── Buttons ────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--green), #00a882);
        color: #080c14; font-weight: 700; border: none;
        border-radius: 8px; font-family: 'Syne', sans-serif;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 18px rgba(0,212,170,0.3);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--green), #00a882);
        color: #080c14; font-weight: 700; border: none;
        border-radius: 8px; font-family: 'Syne', sans-serif;
        transition: all 0.2s; padding: 0.6rem 1.8rem;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 18px rgba(0,212,170,0.3);
    }

    /* ── Widgets ────────────────────────────────────── */
    .stExpander {
        background: var(--card); border: 1px solid var(--border);
        border-radius: 10px; margin: 5px 0;
    }
    .stMetric { background: var(--card); border-radius: 10px; padding: 1rem; }
    .stMetric label { color: var(--muted); font-size: 0.78rem; }
    .stMetric [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 800; }
    [data-testid="stFileUploader"] {
        background: var(--surface);
        border: 2px dashed var(--green);
        border-radius: 12px; padding: 2rem;
    }
    .stProgress > div > div { background: var(--green); }
    .stDataFrame { background: var(--card); border-radius: 10px; }
    .stMultiSelect > div > div { background: var(--surface); border-color: var(--border); }
    </style>
    """, unsafe_allow_html=True)