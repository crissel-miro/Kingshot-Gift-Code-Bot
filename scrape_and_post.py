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

    # Primary strategy: only look at the text between "Active Codes" and
    # "Concierge" (the actual codes section on the page). This avoids
    # accidentally matching unrelated "...Copy" buttons elsewhere on the page
    # (ads, tracking scripts, share widgets, etc.) that aren't real gift codes.
    page_text = soup.get_text(separator="\n")
    match = re.search(r"Active Codes:?(.*?)Concierge", page_text, re.S | re.I)
    if match:
        section = match.group(1)
        found = re.findall(r"\b([A-Za-z0-9]{4,25})\s*Copy\b", section, re.I)
        codes = sorted(set(found))
        if codes:
            return codes

    # Fallback strategy (only used if the section above wasn't found at all,
    # e.g. the site's heading wording changed): scan every <li> on the page.
    codes = set()
    for li in soup.find_all("li"):
        text = li.get_text(separator=" ", strip=True)
        m = re.match(r"^([A-Za-z0-9]{4,25})\s*copy$", text, re.I)
        if m:
            codes.add(m.group(1))

    if not codes:
        print("Could not find any gift codes — site layout may have changed.")
    return sorted(codes)


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def post_to_discord(new_codes):
    codes_block = "\n".join(f"🎁 `{c}`" for c in new_codes)

    plural = len(new_codes) > 1
    header_suffix = "S" if plural else ""
    content = (
        f"📢 **NEW KINGSHOT GIFT CODE{header_suffix}!** 🎁\n\n"
        f"New **Gift Code{'s' if plural else ''}** ha{'ve' if plural else 's'} been released:\n"
        f"{codes_block}\n\n"
        f"Don't miss out on your free rewards.\n\n"
        f"🎁 **Redeem your code:**\n"
        f"https://ks-giftcode.centurygame.com/\n\n"
        f"⏰ **Gift codes can expire quickly, so redeem them as soon as possible!**\n\n"
        f"🏎️ **RDK N CHILL.**"
    )
    resp = requests.post(WEBHOOK_URL, json={"content": content}, timeout=20)
    resp.raise_for_status()

    # Follow up with each code as its own standalone message containing
    # nothing but the code itself. On mobile, long-pressing a message only
    # copies that message's exact text, so this makes copying just the code
    # (with nothing else attached) reliable.
    for code in new_codes:
        resp = requests.post(WEBHOOK_URL, json={"content": code}, timeout=20)
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
