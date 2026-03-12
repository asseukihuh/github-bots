import datetime as dt
import os
import random
import subprocess
import uuid
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    process = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return process.stdout.strip()


def _repo_dir() -> Path:
    return Path(os.getenv("TARGET_REPO_DIR", "./target-repo")).resolve()


def _ensure_repo() -> Path:
    repo_url = os.getenv("TARGET_REPO_URL", "").strip()
    repo_dir = _repo_dir()

    if not repo_url:
        raise ValueError("TARGET_REPO_URL is required in environment.")

    if not repo_dir.exists():
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", repo_url, str(repo_dir)])

    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        raise ValueError(f"TARGET_REPO_DIR exists but is not a git repo: {repo_dir}")

    _run(["git", "fetch", "origin"], cwd=repo_dir)
    _run(["git", "pull", "--rebase"], cwd=repo_dir)

    user_name = os.getenv("GIT_USER_NAME", "Auto Commit Bot")
    user_email = os.getenv("GIT_USER_EMAIL", "bot@example.com")
    _run(["git", "config", "user.name", user_name], cwd=repo_dir)
    _run(["git", "config", "user.email", user_email], cwd=repo_dir)

    return repo_dir


def _random_commit_time_for_today() -> dt.datetime:
    now = dt.datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    random_seconds = random.randint(0, int((end - start).total_seconds()))
    return start + dt.timedelta(seconds=random_seconds)


def _append_heartbeat(repo_dir: Path, commit_time: dt.datetime) -> None:
    heartbeat_file = os.getenv("HEARTBEAT_FILE", ".auto-commit-heartbeat")
    path = repo_dir / heartbeat_file
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(f"{commit_time.isoformat()} | {uuid.uuid4()}\\n")


def _create_commit(repo_dir: Path, commit_time: dt.datetime, index: int, total: int) -> None:
    _append_heartbeat(repo_dir, commit_time)
    _run(["git", "add", "."], cwd=repo_dir)

    message_prefix = os.getenv("COMMIT_MESSAGE_PREFIX", "chore: daily activity")
    message = f"{message_prefix} ({index}/{total})"

    env = os.environ.copy()
    date_string = commit_time.strftime("%Y-%m-%dT%H:%M:%S")
    env["GIT_AUTHOR_DATE"] = date_string
    env["GIT_COMMITTER_DATE"] = date_string

    _run(["git", "commit", "-m", message], cwd=repo_dir, env=env)


def run_auto_commit() -> dict:
    repo_dir = _ensure_repo()

    min_commits = int(os.getenv("MIN_COMMITS", "1"))
    max_commits = int(os.getenv("MAX_COMMITS", "5"))
    if min_commits < 0 or max_commits < 0:
        raise ValueError("MIN_COMMITS and MAX_COMMITS must be >= 0")
    if min_commits > max_commits:
        raise ValueError("MIN_COMMITS cannot be greater than MAX_COMMITS")

    count = random.randint(min_commits, max_commits)

    if count == 0:
        return {"commits_created": 0, "message": "No commits created (range selected 0)."}

    for index in range(1, count + 1):
        commit_time = _random_commit_time_for_today()
        _create_commit(repo_dir, commit_time, index, count)

    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    _run(["git", "push", "origin", branch], cwd=repo_dir)

    return {
        "commits_created": count,
        "branch": branch,
        "repo_dir": str(repo_dir),
    }


if __name__ == "__main__":
    result = run_auto_commit()
    print(result)
