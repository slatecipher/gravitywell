import os

from gravitywell import AsyncPiHole, PiHoleAuth
from gravitywell.mcp import create_server

api = AsyncPiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))
server = create_server(api, areas=["insights", "stats", "queries", "dns"], allow_writes=True)


@server.tool
def household() -> str:
    """Describe the household network: who uses which device."""
    return "192.168.1.50 is the kids' tablet; 192.168.1.20 is the work laptop."


if __name__ == "__main__":
    server.run()  # stdio; the server logs out of the Pi-hole when it stops
