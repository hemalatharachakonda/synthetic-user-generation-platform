import streamlit as st
from utils.state_manager import init_session_state, has_personas
from components.visualizations import adoption_chart, sentiment_donut, theme_bars
from services.api_client import extract_insights
from styles.theme import load_css

st.set_page_config(page_title="Insights Dashboard", page_icon="📊", layout="wide")
init_session_state()

css = load_css("styles/custom.css")
if css:
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

st.markdown('<div class="eyebrow">Findings</div>', unsafe_allow_html=True)
st.title("📊 Insights Dashboard")

if not has_personas():
    st.warning("No personas yet. Create an experiment first.")
    if st.button("📝 Go to Experiment Workspace"):
        st.switch_page("pages/1_Experiment_Workspace.py")
    st.stop()

st.caption(f"Experiment: **{st.session_state.experiment['product_name']}**")

if st.button("🔄 Recalculate Insights") or st.session_state.insights is None:
    with st.spinner("Extracting insights..."):
        st.session_state.insights = extract_insights(
            st.session_state.personas,
            st.session_state.survey_responses,
            st.session_state.chat_history,
        )

insights = st.session_state.insights

col1, col2 = st.columns(2)
col1.metric("Would Use", f"{insights['would_use_pct']}%")
col2.metric("Would Pay", f"{insights['would_pay_pct']}%")

st.markdown('<div class="section-label">Theme Clusters & Sentiment</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    theme_bars(insights["themes"])
with c2:
    sentiment_donut(insights["sentiment"])

st.markdown('<div class="section-label">Adoption by Persona</div>', unsafe_allow_html=True)
adoption_chart(st.session_state.personas)

st.markdown('<div class="section-label">Key Quotes</div>', unsafe_allow_html=True)
for q in insights.get("key_quotes", []):
    st.markdown(
        f"""
        <div class="specimen-card">
            <div style="font-family: var(--font-display); font-style: italic; font-size: 1.05rem;">
                \u201c{q['quote']}\u201d
            </div>
            <div class="specimen-meta" style="margin-top: 0.3rem;">— {q['persona']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
if st.button("📄 Generate Full Report", type="primary"):
    st.switch_page("pages/6_Report_Generator.py")
