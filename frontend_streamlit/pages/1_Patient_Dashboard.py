import streamlit as st
import sys
import plotly.express as px
from datetime import datetime
from pathlib import Path

# Fix relative import paths
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from frontend_streamlit.services.api_client import analyze_patient, call_chatbot_api, fetch_risk_history
from frontend_streamlit.services.charts import render_risk_gauge
from frontend_streamlit.services.pdf_generator import generate_clinical_pdf

st.set_page_config(page_title="Patient Dashboard", page_icon="👩‍🍼", layout="wide")

if not st.session_state.get("authenticated"):
    st.warning("Please login first")
    st.stop()

st.markdown('<div class="page-header"><h1>👩‍🍼 Patient Dashboard</h1><p>Comprehensive maternal risk assessment and monitoring</p></div>', unsafe_allow_html=True)

col_form, col_viz = st.columns([1.2, 0.8], gap="large")

with col_form:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📋 Clinical Assessment Form")
    
    with st.form("risk_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Age", 13, 55, 30)
            trimester = st.selectbox("Trimester", [1,2,3])
            trimester_weeks = st.number_input("Weeks", 1, 42, 32)
            systolic = st.number_input("Systolic BP", 50, 300, 120)
            diastolic = st.number_input("Diastolic BP", 30, 200, 80)
            hemoglobin = st.number_input("Hemoglobin", 0.0, 25.0, 11.5)
            heart_rate = st.number_input("Heart Rate", 40, 200, 85)

        with c2:
            swelling = st.checkbox("Swelling / Edema")
            headache_severity = st.slider("Headache Severity (0-3)", 0, 3, 0)
            vaginal_bleeding = st.checkbox("Vaginal Bleeding")
            diabetes_history = st.checkbox("Diabetes History")
            previous_complications = st.checkbox("Previous Complications")
            fever = st.checkbox("Fever")
            blurred_vision = st.checkbox("Blurred Vision")
            reduced_fetal_movement = st.checkbox("Reduced Fetal Movement")
            severe_abdominal_pain = st.checkbox("Severe Abdominal Pain")

        submit = st.form_submit_button("🔍 Run Full Analysis", width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

if submit:
    with st.spinner("🧠 AI Engine Analyzing..."):
        payload = {
            "age": age,
            "trimester": trimester,
            "trimester_weeks": trimester_weeks,
            "blood_pressure": 1 if systolic >= 140 or diastolic >= 90 else 0,
            "blood_pressure_systolic": systolic,
            "blood_pressure_diastolic": diastolic,
            "hemoglobin": hemoglobin,
            "heart_rate": heart_rate,
            "swelling": 1 if swelling else 0,
            "headache_severity": headache_severity,
            "vaginal_bleeding": 1 if vaginal_bleeding else 0,
            "diabetes_history": 1 if diabetes_history else 0,
            "previous_complications": 1 if previous_complications else 0,
            "fever": 1 if fever else 0,
            "blurred_vision": 1 if blurred_vision else 0,
            "reduced_fetal_movement": 1 if reduced_fetal_movement else 0,
            "severe_abdominal_pain": 1 if severe_abdominal_pain else 0
        }
        result = analyze_patient(payload)
        st.session_state.last_result = result

with col_viz:
    if "last_result" in st.session_state:
        res = st.session_state.last_result
        risk = res.get("final_risk", "LOW")
        conf = res.get("clinical_confidence", 0)
        
        # --- Top Row: Gauge | Info ---
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.plotly_chart(render_risk_gauge(risk, conf), width="stretch")
        
        tc1, tc2 = st.columns(2)
        # Scale clinical confidence to 100% format if it's a decimal
        display_conf = conf * 100 if conf <= 1.0 else conf
        tc1.metric("Clinical Confidence", f"{display_conf:.1f}%")
        tc2.metric("Assessment Time", datetime.now().strftime("%H:%M:%S"))
        st.markdown('</div>', unsafe_allow_html=True)

        # --- Gemini Explanation ---
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("💡 AI Explanation")
        explanation = res.get("explanation", {})
        
        if explanation.get("status") == "generating_async":
             st.info("🧠 Gemini AI is generating a detailed clinical reasoning... [Async Task Pending]")
             if st.button("🔄 Refresh Explanation"):
                 st.rerun()
        else:
             reasoning = explanation.get("reasoning") or explanation.get("gemini_explanation") or "No explanation provided."
             st.info(reasoning)
        
        # --- PDF Report Button ---
        st.write("---")
        pdf_bytes = generate_clinical_pdf(payload, res)
        st.download_button(
            label="📥 Download Clinical Report (PDF)",
            data=pdf_bytes,
            file_name=f"LittleHeart_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            width="stretch"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- ML Probs | Rule Breakdown ---
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        t1, t2 = st.tabs(["ML Probabilities", "Rule Logic"])
        with t1:
            engine_results = res.get("engine_results", {})
            ml_data = engine_results.get("ml", {})
            probabilities = ml_data.get("probabilities", {})
            
            if probabilities:
                import pandas as pd
                df_probs = pd.DataFrame([{"Risk": k, "Probability": v * 100} for k, v in probabilities.items()])
                fig_probs = px.bar(df_probs, x="Risk", y="Probability", color="Risk", 
                                  color_discrete_map={"LOW": "#16A34A", "MEDIUM": "#F59E0B", "HIGH": "#DC2626", "CRITICAL": "#000000"})
                fig_probs.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_probs, width="stretch")
            else:
                st.write("ML probabilities unavailable.")
        with t2:
            if "rule" in engine_results:
                st.json(engine_results["rule"])
            elif "rule_breakdown" in explanation:
                st.json(explanation["rule_breakdown"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # --- Risk History Chart ---
    history = fetch_risk_history()
    if history:
         st.markdown('<div class="glass-card">', unsafe_allow_html=True)
         st.subheader("📉 Risk History")
         fig_hist = px.line(history, x="date", y="risk_score", markers=True, title="Risk Trend over Time")
         fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
         st.plotly_chart(fig_hist, width="stretch")
         st.markdown('</div>', unsafe_allow_html=True)

    # --- Chatbot Section ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💬 LittleHeart Assistant")
    
    # Initialize session if not exists
    if "chat_session_id" not in st.session_state:
        from frontend_streamlit.services.api_client import init_chat_session
        chat_init = init_chat_session()
        st.session_state.chat_session_id = chat_init.get("session_id")
        st.session_state.chat_state = chat_init.get("state", "START")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            st.session_state.chat_history.append({"role": "assistant", "content": "Hi! I'm LittleHeart Assistant. Let's start your health assessment."})

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    prompt = st.chat_input("Enter your message...")
    
    # Mock Voice Feature
    col_v1, col_v2 = st.columns([0.8, 0.2])
    with col_v2:
        if st.button("🎙️ Speak", help="Simulate Voice-to-Text"):
            st.toast("Listening...", icon="🎤")
            # In a real app, this would use WebRTC or browser STT.
            # Here we mock a symptom-loaded query.
            mock_voice_query = "I have a severe headache and some swelling in my ankles."
            st.session_state.chat_history.append({"role": "user", "content": f"[Voice] {mock_voice_query}"})
            with st.spinner("Processing Voice..."):
                 chat_res = call_chatbot_api(st.session_state.chat_session_id, mock_voice_query)
                 response = chat_res.get("response", "No response.")
                 st.session_state.chat_state = chat_res.get("next_state", "START")
                 st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            chat_res = call_chatbot_api(st.session_state.chat_session_id, prompt)
            response = chat_res.get("response", "No response from assistant.")
            st.session_state.chat_state = chat_res.get("next_state", "START")
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # If assessment finished via chat, offer a refresh or trigger analysis
        if st.session_state.chat_state in ["ANALYZING", "COMPLETE"]:
            st.info("💡 Assessment data collected! Please check the results on the dashboard.")
            
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
