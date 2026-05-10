"""
Fact-Check AI – PDF Fact Checker
Clean flow: Upload → Claims → Results → Report (auto-navigation)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import time
import tempfile
import os
from datetime import datetime


# ── Secrets ───────────────────────────────────────────────────────────────────
def _load_secrets():
    for key in ["OPENROUTER_API_KEY", "TAVILY_API_KEY", "SERPAPI_KEY"]:
        try:
            val = st.secrets.get(key, "")
            if val and "your_" not in val:
                os.environ[key] = val
        except Exception:
            pass

_load_secrets()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fact-Check AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Imports ───────────────────────────────────────────────────────────────────
from utils.pdf_parser import extract_text_from_pdf, get_pdf_metadata
from utils.helpers import load_css, get_status_emoji
from agents.extractor import ClaimExtractorAgent
from agents.search_agent import SearchAgent
from agents.verifier import VerifierAgent
from agents.report_agent import ReportAgent

load_css()

# ── Session state ─────────────────────────────────────────────────────────────
defaults = {
    "step": 0,           # 0=upload, 1=claims, 2=results, 3=report
    "claims": [],
    "results": [],
    "pdf_text": "",
    "pdf_meta": {},
    "uploaded_filename": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

LLM_PROVIDER    = "openrouter"
SEARCH_PROVIDER = "tavily" if os.getenv("TAVILY_API_KEY") else "duckduckgo"
MAX_CLAIMS      = 15


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🔍 Fact-Check AI</h1>
    <p class="header-subtitle">AI-Powered PDF Fact Verification · Detect False, Outdated & Misleading Claims</p>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# STEP INDICATOR
# ═════════════════════════════════════════════════════════════════════════════
steps      = ["📁 Upload", "🔎 Claims", "✅ Results", "📊 Report"]
step_names = ["Upload PDF", "Detected Claims", "Verification Results", "Download Report"]

cols = st.columns(len(steps))
for i, (col, label) in enumerate(zip(cols, steps)):
    active  = i == st.session_state.step
    done    = i < st.session_state.step
    if active:
        col.markdown(f'<div class="step-active">{label}<br><small>{step_names[i]}</small></div>', unsafe_allow_html=True)
    elif done:
        col.markdown(f'<div class="step-done">{label}<br><small>{step_names[i]}</small></div>', unsafe_allow_html=True)
    else:
        col.markdown(f'<div class="step-pending">{label}<br><small>{step_names[i]}</small></div>', unsafe_allow_html=True)

st.markdown('<div class="step-divider"></div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# STEP 0 – UPLOAD
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 0:

    st.markdown("### 📄 Upload your PDF to get started")

    uploaded_file = st.file_uploader(
        "Upload PDF", type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        # Save + extract
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with st.spinner("📖 Reading PDF..."):
            text, _ = extract_text_from_pdf(tmp_path)
            meta     = get_pdf_metadata(tmp_path)

        if not text.strip():
            st.error("❌ Could not extract text. Try a text-based PDF.")
        else:
            st.session_state.pdf_text        = text
            st.session_state.pdf_meta        = meta
            st.session_state.uploaded_filename = uploaded_file.name

            # Show file info
            st.markdown(f"""
            <div class="file-card">
                <span class="file-icon">📄</span>
                <div>
                    <strong>{uploaded_file.name}</strong><br>
                    <small>{uploaded_file.size/1024:.1f} KB &nbsp;·&nbsp; {meta.get('pages','?')} pages &nbsp;·&nbsp; {len(text.split()):,} words</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Extract claims button
            if st.button("🔍 Extract Claims", type="primary", use_container_width=False):
                extractor = ClaimExtractorAgent(provider=LLM_PROVIDER, max_claims=MAX_CLAIMS)
                with st.spinner("🤖 Extracting factual claims..."):
                    claims = extractor.extract_claims(st.session_state.pdf_text)

                if claims:
                    st.session_state.claims  = claims
                    st.session_state.results = []
                    st.session_state.step    = 1   # ← auto navigate
                    st.rerun()
                else:
                    st.warning("⚠️ No verifiable claims found. Try a different PDF.")


# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 – DETECTED CLAIMS
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 1:
    claims = st.session_state.claims
    st.markdown(f"### 🔎 {len(claims)} Factual Claims Detected")
    st.caption(f"From: **{st.session_state.uploaded_filename}**")

    # Type distribution pie
    type_counts = {}
    for c in claims:
        t = c.get("type", "other").title()
        type_counts[t] = type_counts.get(t, 0) + 1

    fig = px.pie(
        names=list(type_counts.keys()),
        values=list(type_counts.values()),
        title="Claim Type Distribution",
        color_discrete_sequence=["#00d4aa","#ff6b6b","#ffd93d","#6bcbff","#c084fc"],
        hole=0.45,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0", height=260, margin=dict(t=40,b=10,l=10,r=10),
    )
    st.plotly_chart(fig, use_container_width=True, key="pie_claims")

    # Claims table
    df = pd.DataFrame([
        {"#": i+1, "Claim": c.get("claim",""), "Type": c.get("type","other").title()}
        for i, c in enumerate(claims)
    ])
    st.dataframe(df, use_container_width=True, hide_index=True,
        column_config={
            "#":     st.column_config.NumberColumn("#", width=40),
            "Claim": st.column_config.TextColumn("Claim", width="large"),
            "Type":  st.column_config.TextColumn("Type",  width="small"),
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next, _ = st.columns([1, 1, 4])

    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

    with col_next:
        if st.button("🚀 Start Verification", type="primary", use_container_width=True):
            searcher = SearchAgent(provider=SEARCH_PROVIDER)
            verifier = VerifierAgent(provider=LLM_PROVIDER)

            results     = []
            prog        = st.progress(0, text="Starting...")
            placeholder = st.empty()

            for i, claim in enumerate(claims):
                pct = int((i / len(claims)) * 100)
                prog.progress(pct, text=f"Verifying {i+1} of {len(claims)}...")
                placeholder.info(f"🔍 _{claim['claim'][:110]}..._")

                evidence = searcher.search(claim["claim"])
                result   = verifier.verify(claim, evidence)
                results.append(result)
                time.sleep(0.15)

            prog.progress(100, text="✅ Done!")
            placeholder.empty()
            st.session_state.results = results
            st.session_state.step    = 2   # ← auto navigate
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 – VERIFICATION RESULTS
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    results    = st.session_state.results
    verified   = sum(1 for r in results if r.get("status") == "VERIFIED")
    inaccurate = sum(1 for r in results if r.get("status") == "INACCURATE")
    false_cnt  = sum(1 for r in results if r.get("status") == "FALSE")
    avg_conf   = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)

    st.markdown("### ✅ Verification Results")
    st.caption(f"From: **{st.session_state.uploaded_filename}**")

    # Metric cards
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📋 Total",       len(results))
    m2.metric("✅ Verified",    verified)
    m3.metric("⚠️ Inaccurate", inaccurate)
    m4.metric("❌ False",       false_cnt)
    m5.metric("🎯 Avg Conf",    f"{avg_conf:.0f}%")

    # Bar chart
    fig2 = go.Figure(go.Bar(
        x=["✅ Verified", "⚠️ Inaccurate", "❌ False"],
        y=[verified, inaccurate, false_cnt],
        marker_color=["#00d4aa","#ffd93d","#ff6b6b"],
        text=[verified, inaccurate, false_cnt],
        textposition="outside",
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0", showlegend=False, height=260,
        margin=dict(t=30,b=20,l=10,r=10),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
    )
    st.plotly_chart(fig2, use_container_width=True, key="bar_results")

    # Filter
    filter_status = st.multiselect(
        "Filter by Status", ["VERIFIED","INACCURATE","FALSE"],
        default=["VERIFIED","INACCURATE","FALSE"],
    )
    filtered = [r for r in results if r.get("status") in filter_status]
    st.markdown(f"**{len(filtered)} claims**")

    # Claim cards
    for idx, result in enumerate(filtered):
        status       = result.get("status", "UNKNOWN")
        emoji        = get_status_emoji(status)
        conf         = result.get("confidence", 0)
        claim_text   = result.get("claim", "")
        color_map    = {"VERIFIED":"#00d4aa","INACCURATE":"#ffd93d","FALSE":"#ff6b6b"}
        border_color = color_map.get(status, "#888")

        with st.expander(f"{emoji} {claim_text[:95]}{'...' if len(claim_text)>95 else ''}", expanded=False):
            col_l, col_r = st.columns([2, 1])

            with col_l:
                st.markdown(f"**📌 Claim:** {claim_text}")
                corrected = result.get("corrected_fact", "")
                if corrected and status in ("FALSE", "INACCURATE"):
                    st.markdown(
                        f'<div class="correction-box"><span class="correction-label">✏️ Correct Fact</span><br>{corrected}</div>',
                        unsafe_allow_html=True,
                    )

                evidence = result.get("evidence", [])
                if evidence:
                    st.markdown("**📚 Sources:**")
                    for ev in evidence[:3]:
                        src     = ev.get("source","Unknown")
                        url     = ev.get("url","#")
                        snippet = ev.get("snippet","")
                        st.markdown(
                            f'<div class="evidence-card"><strong>🔗 <a href="{url}" target="_blank">{src}</a></strong>'
                            f'<br><small>{snippet[:200]}{"..." if len(snippet)>200 else ""}</small></div>',
                            unsafe_allow_html=True,
                        )

            with col_r:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=conf,
                    domain={"x":[0,1],"y":[0,1]},
                    title={"text":"Confidence %","font":{"size":11,"color":"#e2e8f0"}},
                    gauge={
                        "axis":{"range":[0,100],"tickcolor":"#888"},
                        "bar":{"color":border_color},
                        "bgcolor":"rgba(0,0,0,0)",
                        "steps":[
                            {"range":[0,40],"color":"rgba(255,107,107,0.15)"},
                            {"range":[40,70],"color":"rgba(255,217,61,0.15)"},
                            {"range":[70,100],"color":"rgba(0,212,170,0.15)"},
                        ],
                    },
                    number={"suffix":"%","font":{"color":"#e2e8f0"}},
                ))
                fig_g.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=170, margin=dict(t=30,b=5,l=15,r=15),
                )
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{idx}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next, _ = st.columns([1, 1, 4])
    with col_back:
        if st.button("← Back", use_container_width=True, key="back_results"):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("📊 View Report", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 – REPORT
# ═════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    results = st.session_state.results
    st.markdown("### 📊 Fact-Check Report")
    st.caption(f"From: **{st.session_state.uploaded_filename}**")

    report_agent = ReportAgent()
    html_report  = report_agent.to_html(results, st.session_state.uploaded_filename)

    # Single download button
    st.download_button(
        label="⬇️ Download Report",
        data=html_report,
        file_name=f"fact_check_ai_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html",
        type="primary",
        use_container_width=False,
    )

    st.divider()

    # Summary stats
    verified   = sum(1 for r in results if r.get("status") == "VERIFIED")
    inaccurate = sum(1 for r in results if r.get("status") == "INACCURATE")
    false_cnt  = sum(1 for r in results if r.get("status") == "FALSE")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 Total",       len(results))
    m2.metric("✅ Verified",    verified)
    m3.metric("⚠️ Inaccurate", inaccurate)
    m4.metric("❌ False",       false_cnt)

    st.markdown("<br>", unsafe_allow_html=True)

    # Full results table
    df_results = pd.DataFrame([
        {
            "Claim":         (r.get("claim","")[:80]+"..." if len(r.get("claim",""))>80 else r.get("claim","")),
            "Status":        r.get("status","N/A"),
            "Confidence":    r.get("confidence",0),
            "Correct Fact":  (r.get("corrected_fact","") or "—")[:150],
        }
        for r in results
    ])
    st.dataframe(df_results, use_container_width=True, hide_index=True,
        column_config={
            "Confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0, max_value=100, format="%d%%"),
            "Correct Fact": st.column_config.TextColumn("✏️ Correct Fact", width="large"),
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_restart, _ = st.columns([1, 1, 4])
    with col_back:
        if st.button("← Back", use_container_width=True, key="back_report"):
            st.session_state.step = 2
            st.rerun()
    with col_restart:
        if st.button("🔄 New PDF", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()