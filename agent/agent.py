import json
import re
from anthropic import Anthropic
from mcp.registry import get_tool, get_tool_descriptions
from mcp.init_tools import init_tools

# Initialize tools
init_tools()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _extract_json(text: str):
    """
    Robust JSON extractor:
    - Finds the first {...} block
    - Strips markdown fences if present
    """
    if not text:
        return None

    # Remove code fences if any
    text = text.replace("```json", "").replace("```", "").strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Fallback: extract the first JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def run_agent(location: str):
    logs = []
    context = f"Location: {location}"

    tools_desc = get_tool_descriptions()

    for step in range(6):  # allow a few steps
        prompt = f"""
You are a telecom operations AI agent.

Your goal:
- Detect if there is a network issue
- Use tools when needed
- Stop when you have enough information

Available tools (use EXACT names):
{tools_desc}

Current context:
{context}

Rules:
- ALWAYS return VALID JSON only
- No explanations outside JSON
- If enough info → action = "finish"

Output format:
{{
  "thought": "your reasoning",
  "action": "tool_name OR finish",
  "input": "input for tool (usually location)",
  "final_answer": "only when action=finish"
}}
"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as e:
            return {
                "logs": logs + [f"❌ Claude API error: {str(e)}"],
                "result": "Claude call failed"
            }

        raw_output = response.content[0].text if response.content else ""
        logs.append(f"🧠 RAW: {raw_output}")

        parsed = _extract_json(raw_output)

        if not parsed:
            return {
                "logs": logs + ["❌ Failed to parse JSON from Claude"],
                "result": "Parsing failed"
            }

        logs.append(f"🧠 PARSED: {parsed}")

        action = parsed.get("action")

        if action == "finish":
            return {
                "logs": logs,
                "result": parsed.get("final_answer", "Completed")
            }

        tool = get_tool(action)

        if not tool:
            logs.append(f"❌ Unknown tool selected: {action}")
            return {
                "logs": logs,
                "result": "Invalid tool"
            }

        tool_input = parsed.get("input", location)

        try:
            tool_result = tool["function"](tool_input)
        except Exception as e:
            logs.append(f"❌ Tool error: {str(e)}")
            return {
                "logs": logs,
                "result": "Tool execution failed"
            }

        logs.append(f"🔧 Tool {action} → {tool_result}")

        # Update context for next iteration
        context += f"\nUsed {action} → {tool_result}"

    return {
        "logs": logs,
        "result": "Max steps reached without finish"
    }