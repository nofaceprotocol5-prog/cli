# 🤖 GitHub 24/7 Automation System Setup

Complete guide to running the continuous GitHub automation system.

## Quick Start

### 1. Prerequisites

```bash
# Required
- Python 3.8+
- Git
- GitHub Personal Access Token (PAT)

# Install dependencies
pip install requests schedule
```

### 2. Environment Setup

Create a `.env` file or set environment variables:

```bash
# GitHub
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_USERNAME="your_username"

# Email (Gmail)
export GMAIL_ADDRESS="your-email@gmail.com"
export GMAIL_PASSWORD="your-app-password"  # Use app password, not main password

# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Discord
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/WEBHOOK"

# Telegram
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Custom Webhook (optional)
export CUSTOM_WEBHOOK_URL="https://your-webhook.example.com/github"
```

### 3. Generate GitHub PAT

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (full control)
   - `workflow` (manage workflows)
   - `admin:repo_hook` (hooks)
4. Copy token and save securely

### 4. Get Notification Credentials

#### Gmail
1. Enable 2FA on your Google account
2. Create app password: https://myaccount.google.com/apppasswords
3. Use 16-character password

#### Slack
1. Create Incoming Webhook: https://api.slack.com/messaging/webhooks
2. Copy webhook URL

#### Discord
1. Right-click channel → Integrations → Webhooks
2. Create webhook and copy URL

#### Telegram
1. Message @BotFather on Telegram
2. Create new bot, get token
3. Message your bot once
4. Get chat ID: https://api.telegram.org/bot{TOKEN}/getUpdates

### 5. Run Automation

#### Interactive Mode (One-time)
```bash
python scripts/github-repo-discovery.py
```

#### Continuous 24/7 Mode
```bash
python scripts/24-7-github-automation.py
```

The system will:
- Run every 6 hours automatically
- Search for trending repos (FastAPI, Discord bots, CLI tools, etc.)
- Fork them to your account
- Add automated workflows
- Push rebuilt versions to private repos
- Send notifications to all configured channels

### 6. Using Docker (Optional)

```bash
docker build -t github-automation .
docker run -e GITHUB_TOKEN=your_token -e GITHUB_USERNAME=your_username github-automation
```

## Workflow Overview

### What the System Does

```
┌─────────────────────────────────────────────────────────────────┐
│                 24/7 GitHub Automation Flow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Search GitHub API for trending repos every 6 hours         │
│     └─ Filter by language, stars, activity                     │
│                                                                 │
│  2. Fork matched repos to your account                         │
│     └─ Keep original attribution & licensing                   │
│                                                                 │
│  3. Clone forked repos locally                                 │
│     └─ Add GitHub Actions rebuild workflow                     │
│     └─ Push workflow to forked repo                            │
│                                                                 │
│  4. Create private repo for rebuilt version                    │
│     └─ Add ATTRIBUTION.md with source info                     │
│     └─ Push rebuilt code to private repo                       │
│                                                                 │
│  5. Send notifications across all channels                     │
│     └─ Email, Slack, Discord, Telegram, Webhooks              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Automated Workflows

Each forked repo gets:

1. **Auto-Rebuild Workflow** (`.github/workflows/24-7-rebuild.yml`)
   - Runs every 6 hours
   - Installs dependencies
   - Runs tests & builds
   - Uploads artifacts
   - Analyzes code

2. **Upstream Sync Workflow**
   - Syncs with original repo changes
   - Merges updates automatically
   - Pushes to your fork

## Configuration Files

### `.github/workflows/24-7-rebuild.yml`
Automatically added to each forked repo. Rebuilds and tests the code.

### `scripts/github-repo-discovery.py`
Interactive tool to manually search and fork repos.

### `scripts/24-7-github-automation.py`
Main automation script - runs continuously every 6 hours.

### `scripts/notification-system.py`
Handles all notification channels.

## Advanced Features

### Custom Search Queries

Edit `scripts/24-7-github-automation.py`:

```python
queries = [
    "fastapi",
    "telegram bot",
    "discord bot",
    "your custom query here"
]
```

### Languages to Target

```python
languages = ["python", "javascript", "go", "rust"]
```

### Adjust Schedule

Change from 6 hours to different interval:

```python
automation.schedule_automation(queries, languages, interval_hours=3)
```

## Monitoring & Logs

### View Logs
```bash
tail -f /tmp/github-24-7.log
```

### Check Private Repos
Your rebuilt repos are at: `https://github.com/your_username?tab=repositories`

### Monitor Forked Repos
Your forks are at: `https://github.com/your_username/stars`

## Troubleshooting

### "Dependencies lock file is not found"
- The system automatically handles this
- If not, run `npm install` or `pip install -r requirements.txt` in the repo

### "Token not found"
```bash
export GITHUB_TOKEN="your_token"
```

### "Notification failed"
- Check that webhook URLs are correct
- Test credentials individually
- Check rate limits: https://api.github.com/rate_limit

### Webhook Issues
```bash
# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  YOUR_SLACK_WEBHOOK_URL
```

## Rate Limits

- GitHub API: 60 requests/hour (unauthenticated), 5000/hour (authenticated)
- The system paces requests to stay within limits
- Logs show rate limit status

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` file with real tokens
- Use GitHub Secrets for CI/CD
- Rotate tokens regularly
- Use app-specific passwords for Gmail
- Don't share webhook URLs publicly

## License Attribution

All forked repos retain original licenses and attribution.
Rebuilt versions include `ATTRIBUTION.md` pointing to source.

## Next Steps

1. Set up environment variables
2. Test with `python scripts/github-repo-discovery.py`
3. Start continuous mode: `python scripts/24-7-github-automation.py`
4. Monitor logs and notifications
5. Customize search queries as needed

---

**Questions?** Check the logs: `tail -f /tmp/github-24-7.log`

**Ready to automate?** 🚀
