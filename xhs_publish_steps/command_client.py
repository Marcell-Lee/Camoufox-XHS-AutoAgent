import json
import time
import uuid
from typing import Any

from config import SESSION_COMMAND_FILE, SESSION_RESULT_FILE, SESSION_STATUS_FILE


def _read_json(path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def ensure_session_ready() -> None:
    status = _read_json(SESSION_STATUS_FILE)
    if status.get("status") != "ready":
        raise RuntimeError(
            "发布页面守护进程未就绪，请先运行 01_open_publish_page.py"
        )


def send_command(action: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    ensure_session_ready()

    command_id = uuid.uuid4().hex
    command = {
        "id": command_id,
        "action": action,
        "payload": payload or {},
        "created_at": time.time(),
    }
    SESSION_COMMAND_FILE.write_text(
        json.dumps(command, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    deadline = time.time() + timeout
    while time.time() < deadline:
        result = _read_json(SESSION_RESULT_FILE)
        if result.get("id") == command_id:
            if result.get("ok"):
                return result
            raise RuntimeError(result.get("message") or "命令执行失败")
        time.sleep(0.2)

    raise TimeoutError(f"等待命令执行超时: {action}")
