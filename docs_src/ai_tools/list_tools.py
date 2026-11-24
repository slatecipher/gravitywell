import os

from clientx.tools import list_tools
from gravitywell import PiHole, PiHoleAuth

# Creating a client doesn't connect: the tools log in on their first call.
api = PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))

tools = [tool for tool in list_tools(api) if tool.read_only]
for tool in tools:
    print(f"{tool.name}: {tool.description.splitlines()[0]}")
# check_health: Check the Pi-hole's health in one call, and list what's wrong.
# stats_summary: Fetch totals of the Pi-hole's queries, clients and blocklists.
# ...
