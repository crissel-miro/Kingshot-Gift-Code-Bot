import json
import os
import sys
from datetime import datetime, timezone

import requests

URL = "https://kingshot.net/api/gift-codes"
STATE_FILE = "seen_codes.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def get_active_codes():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    payload = resp.json()

    gift_codes = payload.get("data", {}).get("giftCodes", [])
    now = datetime.now(timezone.utc)

    active = []
    for entry in gift_codes:
        code = entry.get("code")
        if not code:
            continue
        expires_at = entry.get("expiresAt")
        if expires_at:
            # "expiresAt" is null for codes with no expiry; otherwise it's an
            # ISO timestamp — skip codes that have already expired.
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_dt < now:
                continue
        active.append(code)

    return sorted(set(active))


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
