from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph
from mcp.registry import get_tool
from mcp.init_tools import init_tools

# Initialize tools
init_tools()


# -------------------------------
# STATE DEFINITION (VERY IMPORTANT)
# -------------------------------
class AgentState(TypedDict, total=False):
    location: str
    logs: List[str]
    complaints: List[str]
    network: Dict[str, Any]
    decision: str
    result: str


# Utility to ensure logs exist
def ensure_logs(state: AgentState) -> AgentState:
    if "logs" not in state or state["logs"] is None:
        state["logs"] = []
    return state


# -------------------------------
# NODE 1: REASONING
# -------------------------------
def reason_node(state: AgentState) -> AgentState:
    state = ensure_logs(state)

    location = state.get("location", "Unknown")
    state["logs"].append(f"🔍 Analyzing situation in {location}...")

    complaints_tool = get_tool("complaints")["function"]
    complaints = complaints_tool(location)

    state["complaints"] = complaints
    state["logs"].append(f"📊 Complaints found: {complaints}")

    return state


# -------------------------------
# NODE 2: NETWORK
# -------------------------------
def network_node(state: AgentState) -> AgentState:
    state = ensure_logs(state)

    location = state.get("location", "Unknown")

    network_tool = get_tool("network_status")["function"]
    network = network_tool(location)

    state["network"] = network
    state["logs"].append(f"📡 Network status: {network}")

    return state


# -------------------------------
# NODE 3: DECISION
# -------------------------------
def decision_node(state: AgentState) -> AgentState:
    state = ensure_logs(state)

    complaints = state.get("complaints", [])
    network = state.get("network", {})

    if complaints and network.get("status") == "degraded":
        state["decision"] = "issue_detected"
        state["logs"].append("⚠️ Issue detected based on correlation")
    else:
        state["decision"] = "no_issue"
        state["logs"].append("✅ No major issue detected")

    return state


# -------------------------------
# NODE 4: ACTION
# -------------------------------
def action_node(state: AgentState) -> AgentState:
    state = ensure_logs(state)

    if state.get("decision") == "issue_detected":
        ticket_tool = get_tool("create_ticket")["function"]

        location = state.get("location", "Unknown")
        issue = f"Outage in {location}"
        ticket = ticket_tool(issue)

        state["result"] = ticket
        state["logs"].append(f"🛠️ Action taken: {ticket}")
    else:
        state["result"] = "No action required"

    return state


# -------------------------------
# BUILD GRAPH (FIXED)
# -------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("reason", reason_node)
    graph.add_node("network", network_node)
    graph.add_node("decision", decision_node)
    graph.add_node("action", action_node)

    graph.set_entry_point("reason")

    graph.add_edge("reason", "network")
    graph.add_edge("network", "decision")
    graph.add_edge("decision", "action")

    # 🔥 IMPORTANT: define END node
    graph.set_finish_point("action")

    return graph.compile()