# Kingshot Gift Code Discord Announcer

Checks the official Kingshot gift codes API every 15 minutes (triggered by
cron-job.org) and posts any **new** code to your Discord channel via webhook,
formatted with tap-to-copy code blocks. No Make.com, no per-task credits.

## How it works (current setup)

1. **cron-job.org** (free, external scheduler) fires every 15 minutes and
   calls GitHub's API to trigger the workflow. This replaced GitHub's
   built-in `schedule:` trigger, which was found to run unpredictably late
   (sometimes hours late) under GitHub's own platform load — cron-job.org
   runs on a much more precise, dedicated schedule.
2. **GitHub Actions** runs `scrape_and_post.py` when triggered.
3. The script calls `https://kingshot.net/api/gift-codes`, a real JSON API
   maintained by the Kingshot.net community, and reads the list of currently
   active codes (automatically ignoring any that have expired).
4. It compares that list against `seen_codes.json` (the codes already
   announced, stored in this repo).
5. Any genuinely new code gets posted to Discord, then added to
   `seen_codes.json`, which the workflow commits back to the repo — so the
   bot remembers state between runs with no external database needed.

## Setup

### 1. Create a Discord webhook
1. In Discord, go to your server → the channel you want codes posted to → **Edit Channel → Integrations → Webhooks → New Webhook**.
2. Name it whatever you like, click **Copy Webhook URL**.

### 2. Create a GitHub repo
1. Go to https://github.com/new, create a new repository (public or private).
2. Add these files, keeping the same folder structure:
   ```
   scrape_and_post.py
   seen_codes.json
   .github/workflows/check-codes.yml
   ```
   Easiest way for the `.github/workflows/check-codes.yml` file specifically:
   use **Add file → Create new file**, and type the full path
   `.github/workflows/check-codes.yml` into the filename box — GitHub creates
   the folders automatically. Paste the file's contents in below.

### 3. Add your webhook as a secret
1. In your repo: **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `DISCORD_WEBHOOK_URL`
3. Value: paste the webhook URL from step 1.

### 4. Set up the external scheduler (cron-job.org)
GitHub's own built-in schedule isn't used anymore (see note above), so this
step is required for the bot to run automatically.

1. **Create a GitHub Personal Access Token:**
   - Go to https://github.com/settings/tokens?type=beta → **Generate new token**
   - Repository access: **Only select repositories** → your repo
   - Permissions → **Actions** → **Read and write**
   - Generate, then copy the token (starts with `github_pat_...`) — shown only once
2. **Create a free account at https://cron-job.org**
3. **Create cronjob:**
   - **URL:** `https://api.github.com/repos/<your-username>/<your-repo-name>/actions/workflows/check-codes.yml/dispatches`
   - **Schedule:** every 15 minutes
   - **Request method:** POST
   - **Headers:**
     - `Authorization` → `Bearer <your token>`
     - `Accept` → `application/vnd.github+json`
     - `Content-Type` → `application/json`
   - **Request body:** `{"ref":"main"}`
   - Save, then click **Test Run** to confirm it returns `204 No Content`

### 5. Enable the workflow
1. Go to the **Actions** tab of your repo. If prompted, click "I understand my workflows, enable them."
2. You'll see "Check Kingshot Gift Codes" listed.
3. To test manually any time: click into the workflow → **Run workflow** button.

## Adjusting the schedule
Change the interval on cron-job.org directly (not in the GitHub workflow
file anymore, since that trigger is disabled). Their free plan supports
intervals as short as every 1 minute, though every 15 minutes is a
reasonable default for this use case.

## Message format
Edit the `post_to_discord()` function in `scrape_and_post.py` to change the
Discord announcement's wording, emojis, or layout. Each new code renders as
a tappable inline code block (`` `KS0715` ``) for easy copying.

## Cost
Completely free:
- **cron-job.org:** free for schedules as frequent as every 1 minute.
- **GitHub Actions:** each run takes only a few seconds.
  - Public repos: unlimited free minutes.
  - Private repos: 2,000 free minutes/month. Running every 15 minutes uses
    roughly 200–300 minutes/month at a few seconds per run — comfortably
    within the free tier under normal conditions. If you ever see minutes
    running low, check that only **one** scheduler is active (this repo
    should rely on cron-job.org only, not GitHub's own `schedule:` trigger,
    since running both at once roughly doubles usage). Making the repo
    public removes this limit entirely.

## Known limitations
- If kingshot.net changes their API's response format, the script may need
  updating to match the new structure.
- `seen_codes.json` only ever grows (codes are added, never removed) — the
  bot does not detect or announce when a code is removed/expired on the
  source, only when a new one appears.
