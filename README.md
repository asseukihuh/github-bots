# GitHub Auto-Commit Bot (Python)

This bot creates a random number of commits per day in a target repository.

No webhook server is used. The flow is:

1. `cron-job.org` calls GitHub API (`workflow_dispatch`)
2. GitHub Actions runs `bot.py`
3. `bot.py` clones target repo, creates random commits, and pushes

## Files

- `bot.py` commit engine (random range + push)
- `.github/workflows/auto-commit.yml` GitHub Actions entrypoint
- `.env.example` local/dev config example

## Required GitHub Secrets (in this bot repo)

Go to **Repo Settings → Secrets and variables → Actions → New repository secret** and add:

- `TARGET_REPO_URL` (recommended tokenized HTTPS URL)
	- Example: `https://x-access-token:YOUR_PAT@github.com/YOUR_USERNAME/YOUR_REPO.git`
- `GIT_USER_NAME`
- `GIT_USER_EMAIL`
- `MIN_COMMITS` (example `1`)
- `MAX_COMMITS` (example `5`)
- `HEARTBEAT_FILE` (example `.auto-commit-heartbeat`)
- `COMMIT_MESSAGE_PREFIX` (example `chore: daily activity`)

Also create a PAT token for cron-job.org to trigger workflow:

- `CRON_TRIGGER_PAT` with at least repo/workflow access for this bot repo.

## cron-job.org setup

Create a job in cron-job.org:

- Method: `POST`
- URL: `https://api.github.com/repos/YOUR_USERNAME/YOUR_BOT_REPO/actions/workflows/auto-commit.yml/dispatches`
- Header 1: `Accept: application/vnd.github+json`
- Header 2: `Authorization: Bearer YOUR_CRON_TRIGGER_PAT`
- Header 3: `X-GitHub-Api-Version: 2022-11-28`
- Header 4: `Content-Type: application/json`
- Body:

```json
{"ref":"main"}
```

- Schedule: your desired daily cron expression/time.

## Local test (optional)

```bash
python bot.py
```

Use `.env` for local run (`Copy-Item .env.example .env` on PowerShell).

## Notes

- Keep all tokens in GitHub Secrets, never in code.
- If target repo is private, use a PAT in `TARGET_REPO_URL`.
- If you set `MIN_COMMITS=0`, some runs can create zero commits.

