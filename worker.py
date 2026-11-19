"""Detached Codex task runner with atomic result persistence."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time


def save(path: Path, value: dict) -> None:
    """Atomically replace a JSON record."""
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def identity(pid: int) -> str:
    """Read process start time to protect against PID reuse."""
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    if fields[0] == "Z":
        raise ProcessLookupError(pid)
    return fields[19]


def run(directory: Path) -> None:
    """Execute one persisted request and record terminal status."""
    request = json.loads((directory / "request.json").read_text())
    save(directory / "process.json", {"pid": os.getpid(), "identity": identity(os.getpid())})
    result = {"status": "failed", "thread_id": "", "output": "", "exit_code": None}
    turn_messages = []
    last_completed_message = ""
    try:
        command = [request["cli"], "exec"]
        if request.get("thread_id"):
            command += ["resume", "--skip-git-repo-check", "--json", request["thread_id"]]
        else:
            command += ["--skip-git-repo-check", "--json", "-C", request["project"]]
        command += ["-"]
        with (directory / "stderr.log").open("w") as errors, (directory / "events.jsonl").open("w") as events:
            process = subprocess.Popen(command, cwd=request["project"], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=errors, text=True)
            process.stdin.write(request["prompt"])
            process.stdin.close()
            completed = False
            for line in process.stdout:
                events.write(line)
                events.flush()
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("type") == "thread.started":
                    result["thread_id"] = event["thread_id"]
                event_type = event.get("type")
                if event_type == "turn.started":
                    turn_messages = []
                if event_type == "turn.completed":
                    completed = True
                    last_completed_message = turn_messages[-1] if turn_messages else ""
                    turn_messages = []
                if event_type in {"turn.failed", "error"}:
                    result["error"] = event.get("error", event)
                item = event.get("item", {})
                if event_type == "item.completed" and item.get("type") == "agent_message":
                    turn_messages.append(item.get("text", ""))
            result["exit_code"] = process.wait()
            result["status"] = "completed" if completed and process.returncode == 0 and "error" not in result else "failed"
        result["output"] = last_completed_message[-16000:]
        if not result["output"]:
            result["output"] = (directory / "stderr.log").read_text()[-4000:]
    except Exception as exc:
        result["error"] = str(exc)
    result["finished_at"] = time.time()
    save(directory / "result.json", result)


if __name__ == "__main__":
    run(Path(sys.argv[1]))
