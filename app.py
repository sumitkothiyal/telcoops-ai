import streamlit as st
from agent.multi_agent import run_multi_agent

st.set_page_config(page_title="TelcoOps AI", layout="wide")

st.title("📡 TelcoOps AI - Autonomous Agent System")

location = st.selectbox("Select Location", ["Dallas", "New York"])

scenario = st.selectbox(
    "Select Scenario",
    ["Normal Day", "Peak Traffic", "Local Outage", "Major Outage"]
)

if st.button("Run Autonomous Agent"):
    input_data = f"{location} | {scenario}"

    result = run_multi_agent(input_data)

    st.subheader("🧠 Agent Reasoning Flow (Agentic AI)")
    for log in result.get("logs", []):
        st.write(log)

    st.subheader("📊 Final Autonomous Decision")
    st.write(result.get("result"))