tools = {}

def register_tool(name, func, description):
    tools[name] = {
        "function": func,
        "description": description
    }

def get_tool(name):
    return tools.get(name)

def list_tools():
    return tools


# 🔥 NEW: tool descriptions for LLM
def get_tool_descriptions():
    desc = []
    for name, tool in tools.items():
        desc.append(f"{name}: {tool['description']}")
    return "\n".join(desc)