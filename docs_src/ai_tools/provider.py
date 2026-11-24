import json
import os
from typing import Any

from clientx.tools import ToolError, list_tools
from gravitywell import PiHole, PiHoleAuth

api = PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))
tools = {tool.name: tool for tool in list_tools(api) if tool.read_only or "dns" in tool.tags}

# Anthropic's Messages API takes these as `tools=`.
# Other providers take the same three fields, wrapped their own way.
definitions = [
    {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
    for tool in tools.values()
]


def run_tool(name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
    """Run the tool a model asked for: its result as JSON, and whether it failed."""
    try:
        return json.dumps(tools[name].call(arguments)), False
    except ToolError as error:
        return str(error), True  # what went wrong, for the model: never the session or the password


print(run_tool("dns_blocking", {}))
