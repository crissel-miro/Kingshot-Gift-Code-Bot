import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

URL = "https://kingshotwiki.com/giftcodes/"
STATE_FILE = "seen_codes.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def get_active_codes():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(separator="\n")

    # The site lists codes between "Active Codes:" and "Concierge member codes:",
    # each one immediately followed by the word "Copy" (a copy-button label).
    match = re.search(r"Active Codes:(.*?)Concierge member codes:", page_text, re.S)
    if not match:
        print("Could not find the 'Active Codes' section — site layout may have changed.")
        return []

    section = match.group(1)
    codes = re.findall(r"\b([A-Za-z0-9]{4,})Copy", section)
    return sorted(set(codes))


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def post_to_discord(new_codes):
    lines = "\n".join(f"🎁 `{c}`" for c in new_codes)
    content = (
        f"**New Kingshot gift code(s) found!**\n{lines}\n"
        f"Redeem here: https://ks-giftcode.centurygame.com/"
    )
    resp = requests.post(WEBHOOK_URL, json={"content": content}, timeout=20)
    resp.raise_for_status()


def main():
    if not WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable is not set.")
        sys.exit(1)

    current = set(get_active_codes())
    if not current:
        print("No codes found on the page at all — skipping this run.")
        return

    seen = load_seen()
    new_codes = current - seen

    if new_codes:
        post_to_discord(sorted(new_codes))
        save_seen(seen | new_codes)
        print(f"Posted {len(new_codes)} new code(s): {sorted(new_codes)}")
    else:
        print("No new codes since last check.")


if __name__ == "__main__":
    main()
