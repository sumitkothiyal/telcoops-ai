from anthropic import Anthropic
from mcp.registry import get_tool, list_tools
from mcp.init_tools import init_tools
import json
import re
import os

# Initialize tools
init_tools()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# -----------------------------
# Utility: Safe JSON parser
# -----------------------------
def extract_json(text):
    if not text:
        return None

    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                return None
    return None


# -----------------------------
# 🧠 AUTONOMOUS AGENT LOOP
# -----------------------------
def run_multi_agent(input_data):
    logs = []
    context = f"Initial Input: {input_data}"

    # MCP tool discovery
    available_tools = list(list_tools().keys())
    logs.append(f"🔌 MCP Registry Loaded Tools: {available_tools}")

    for step in range(6):
        prompt = f"""
You are an autonomous telecom AI agent.

Your goal:
- Detect network issues
- Decide next best action
- Use tools only when needed
- Stop when you have enough information

Available tools:
{available_tools}

Context so far:
{context}

STRICT INSTRUCTIONS:
- Think step-by-step
- Choose ONE action at a time
- Respond ONLY in VALID JSON

Format:
{{
  "thought": "reasoning",
  "action": "tool_name OR finish",
  "input": "input for tool",
  "final_answer": "only if action = finish"
}}
"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text if response.content else ""
        logs.append(f"🧠 Agent Thought RAW: {raw}")

        parsed = extract_json(raw)

        if not parsed:
            return {
                "logs": logs,
                "result": "Failed to parse agent response"
            }

        thought = parsed.get("thought")
        action = parsed.get("action")

        logs.append(f"🧠 Agent Decision: {thought}")

        # Finish condition
        if action == "finish":
            return {
                "logs": logs,
                "result": parsed.get("final_answer", "Completed")
            }

        tool = get_tool(action)

        if not tool:
            logs.append(f"❌ Invalid tool selected: {action}")
            return {
                "logs": logs,
                "result": "Invalid tool"
            }

        tool_input = parsed.get("input", input_data)

        # MCP tool call
        logs.append(f"🔌 MCP Call → Tool: {action} | Input: {tool_input}")

        try:
            result = tool["function"](tool_input)
        except Exception as e:
            logs.append(f"❌ Tool execution error: {str(e)}")
            return {
                "logs": logs,
                "result": "Tool failure"
            }

        logs.append(f"📡 Tool Response → {result}")

        # Update context
        context += f"\nUsed {action} → {result}"

    return {
        "logs": logs,
        "result": "Max steps reached without conclusion"
    }