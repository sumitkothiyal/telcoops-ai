from mcp.registry import register_tool
from tools.network import get_network_status
from tools.complaints import get_complaints
from tools.ticketing import create_ticket


def init_tools():
    register_tool("network_status", get_network_status, "Check network status")
    register_tool("complaints", get_complaints, "Fetch complaints")
    register_tool("create_ticket", create_ticket, "Create ticket")