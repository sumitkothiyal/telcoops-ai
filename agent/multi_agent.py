from anthropic import Anthropic
from mcp.registry import get_tool
from mcp.init_tools import init_tools
import json
import re
import os

# Initialize tools
init_tools()

# Load API key securely
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# -----------------------------
# Utility: Safe JSON parser
# -----------------------------
def extract_json(text):
    if not text:
        return None

    text = text.replace("```json", "").replace("```", "").strip()

    # Try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # Extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None

    return None


# -----------------------------
# 🧠 PLANNER AGENT
# -----------------------------
def planner_agent(input_data):
    prompt = f"""
You are a telecom planning agent.

Goal:
Create a step-by-step plan to investigate network issues.

Available tools (use EXACT names):
- complaints
- network_status
- create_ticket

STRICT INSTRUCTIONS:
- Respond ONLY in VALID JSON
- No explanation outside JSON

Format:
{{
  "plan": ["complaints", "network_status", "create_ticket"]
}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text if response.content else ""
    parsed = extract_json(raw)

    if not parsed or "plan" not in parsed:
        return {"plan": ["complaints", "network_status", "create_ticket"]}

    return parsed


# -----------------------------
# ⚙️ EXECUTOR AGENT
# -----------------------------
def executor_agent(plan, input_data, logs):
    context = ""

    for step in plan:
        tool = get_tool(step)

        if not tool:
            logs.append(f"❌ Unknown step: {step}")
            continue

        try:
            result = tool["function"](input_data)
        except Exception as e:
            logs.append(f"❌ Tool error in {step}: {str(e)}")
            continue

        logs.append(f"🔧 Executed {step} → {result}")
        context += f"\n{step}: {result}"

    return context


# -----------------------------
# 🔍 CRITIC AGENT (FIXED)
# -----------------------------
def critic_agent(context, logs):
    prompt = f"""
You are a telecom QA agent.

Context:
{context}

Rules:
- If complaints are high AND network is degraded/down → confirm outage
- If complaints are low but network degraded → monitor, not immediate escalation
- Always provide clear conclusion

STRICT INSTRUCTIONS:
- Respond ONLY in VALID JSON
- No explanation outside JSON
- JSON must be parseable

Format:
{{
  "final_answer": "clear conclusion",
  "confidence": "high/medium/low",
  "recommendation": "next action"
}}
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
    except Exception as e:
        return {
            "final_answer": "Critic failed",
            "confidence": "low",
            "recommendation": f"Error: {str(e)}"
        }

    raw = response.content[0].text if response.content else ""
    logs.append(f"🧠 Critic RAW: {raw}")

    parsed = extract_json(raw)

    # 🔥 Smart fallback if parsing fails
    if not parsed:
        return {
            "final_answer": "Network degradation detected but model response was unstructured",
            "confidence": "medium",
            "recommendation": "Investigate further and validate telemetry"
        }

    return parsed


# -----------------------------
# MAIN MULTI-AGENT FLOW
# -----------------------------
def run_multi_agent(input_data):
    logs = []

    # Planner
    logs.append("🧠 Planner: Creating investigation plan...")
    plan_output = planner_agent(input_data)

    plan = plan_output.get("plan", [])
    logs.append(f"📋 Plan: {plan}")

    # Executor
    logs.append("⚙️ Executor: Running steps...")
    context = executor_agent(plan, input_data, logs)

    # Critic
    logs.append("🔍 Critic: Evaluating results...")
    final = critic_agent(context, logs)

    return {
        "logs": logs,
        "plan": plan,
        "analysis": final
    }