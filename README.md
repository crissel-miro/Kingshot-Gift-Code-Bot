# Kingshot Gift Code Discord Announcer (Free — GitHub Actions)

Checks https://kingshotwiki.com/giftcodes/ every 15 minutes and posts any **new**
gift code to your Discord channel via webhook. No Make.com, no credits, no server.

## Setup (5 minutes)

### 1. Create a Discord webhook
1. In Discord, go to your server → the channel you want codes posted to → **Edit Channel → Integrations → Webhooks → New Webhook**.
2. Name it whatever you like, click **Copy Webhook URL**.

### 2. Create a GitHub repo
1. Go to https://github.com/new, create a new repository (public or private, either works).
2. Upload these 4 files/folders keeping the same structure:
   ```
   scrape_and_post.py
   seen_codes.json
   .github/workflows/check-codes.yml
   ```
   (Easiest: on the repo page, use "Add file → Upload files" and drag the whole folder, or use `git push` if you're comfortable with git.)

### 3. Add your webhook as a secret
1. In your repo: **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `DISCORD_WEBHOOK_URL`
3. Value: paste the webhook URL from step 1.

### 4. Turn it on
1. Go to the **Actions** tab of your repo. If prompted, click "I understand my workflows, enable them."
2. You'll see "Check Kingshot Gift Codes" listed. It will now run automatically every 30 minutes.
3. To test it immediately: click on the workflow → **Run workflow** button (this is the `workflow_dispatch` trigger).

## How it works
- `scrape_and_post.py` downloads the gift code page, pulls out the codes listed under "Active Codes", and compares them against `seen_codes.json` (the codes it has already announced).
- Any code that's new gets posted to Discord, then added to `seen_codes.json`, which the workflow commits back to your repo — so the bot remembers state between runs without any external database.

## Adjusting the schedule
Edit the `cron` line in `.github/workflows/check-codes.yml`. Examples:
- `*/15 * * * *` → every 15 minutes
- `0 * * * *` → once an hour
- `0 */6 * * *` → every 6 hours

(Note: GitHub's scheduled triggers can run a few minutes late during high load — this is a platform limitation, not a bug in the script.)

## Cost
Completely free for this use case:
- Public repos: unlimited GitHub Actions minutes.
- Private repos: 2,000 free minutes/month — this job takes well under a minute per run, so even checking every 15 minutes uses a small fraction of that.
