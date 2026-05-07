import streamlit as st
from agent.multi_agent import run_multi_agent

st.set_page_config(page_title="TelcoOps AI", layout="wide")

st.title("📡 TelcoOps AI - Multi-Agent System")

location = st.selectbox("Select Location", ["Dallas", "New York"])

scenario = st.selectbox(
    "Select Scenario",
    ["Normal Day", "Peak Traffic", "Local Outage", "Major Outage"]
)

if st.button("Run Multi-Agent"):
    input_data = f"{location} | {scenario}"

    result = run_multi_agent(input_data)

    st.subheader("🧠 Agent Logs")
    for log in result.get("logs", []):
        st.write(log)

    st.subheader("📋 Plan")
    st.write(result.get("plan"))

    st.subheader("📊 Final Analysis")
    st.json(result.get("analysis"))