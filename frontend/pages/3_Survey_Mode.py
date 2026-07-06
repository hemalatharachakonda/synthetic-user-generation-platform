import streamlit as st
from utils.state_manager import init_session_state, has_personas
from utils.constants import MAX_SURVEY_QUESTIONS
from components.survey_grid import survey_grid
from services.api_client import create_survey, execute_survey, get_survey_responses
from styles.theme import load_css

st.set_page_config(page_title="Survey Mode", page_icon="📊", layout="wide")
init_session_state()

css = load_css("styles/custom.css")
if css:
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

st.markdown('<div class="eyebrow">Structured Questionnaire</div>', unsafe_allow_html=True)
st.title("📊 Survey Mode")

if not has_personas():
    st.warning("No personas yet. Create an experiment first.")
    if st.button("📝 Go to Experiment Workspace"):
        st.switch_page("pages/1_Experiment_Workspace.py")
    st.stop()

st.caption(f"Experiment: **{st.session_state.experiment['product_name']}**")

if not st.session_state.survey_questions:
    st.markdown('<div class="section-label">Set Up Your Survey</div>', unsafe_allow_html=True)
    default_q = "How likely are you to use this product?"
    with st.form("question_setup"):
        q_text = st.text_area(
            "Enter one question per line (max %d)" % MAX_SURVEY_QUESTIONS,
            value=default_q, height=100,
        )
        start = st.form_submit_button("Start Survey", type="primary")
    if start:
        questions = [q.strip() for q in q_text.split("\n") if q.strip()][:MAX_SURVEY_QUESTIONS]
        if not questions:
            st.error("Please enter at least one question.")
        else:
            st.session_state.survey_questions = questions
            # Create survey in backend
            with st.spinner("Creating survey..."):
                experiment_id = st.session_state.experiment.get("id", "")
                survey = create_survey(experiment_id, "User Feedback Survey", questions)
                st.session_state.current_survey = survey
            
            # Execute survey to generate all responses
            with st.spinner("Generating persona responses..."):
                survey_id = survey.get("id", "")
                result = execute_survey(survey_id)
                st.session_state.survey_responses = result.get("persona_responses", [])
                st.session_state.current_question_index = 0
            
            st.success("Survey completed! All persona responses generated.")
            st.rerun()
    st.stop()

# Display all survey responses
st.markdown('<div class="section-label">Survey Results</div>', unsafe_allow_html=True)

if st.session_state.survey_responses:
    for persona_response in st.session_state.survey_responses:
        st.markdown(f"### {persona_response.get('persona_name', 'Unknown')}")
        for idx, response in enumerate(persona_response.get('responses', [])):
            st.markdown(f"**Q{idx + 1}:** {response.get('question', '')}")
            st.markdown(f"**A:** {response.get('answer', '')}")
            st.markdown(f"*Confidence: {response.get('confidence', 0):.2f}*")
            st.divider()

st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Reset Survey"):
        st.session_state.survey_questions = []
        st.session_state.survey_responses = []
        st.session_state.current_survey = None
        st.rerun()
with col2:
    if st.button("📈 View Insights"):
        st.switch_page("pages/5_Insights_Dashboard.py")
