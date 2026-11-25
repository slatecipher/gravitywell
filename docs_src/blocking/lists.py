import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    api.lists.add("block", "https://example.com/hosts.txt", comment="Example blocklist")

    # A new list takes effect after a gravity update,
    # which downloads every list again and can take minutes.
    update = api.action.update_gravity()
    print("Gravity updated" if update.succeeded else update.output)

    for subscribed in api.lists.list("block").lists:
        print(f"{subscribed.number:>9,} domains  {subscribed.address}")
