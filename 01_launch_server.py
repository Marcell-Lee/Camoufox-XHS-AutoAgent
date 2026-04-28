"""
Start the Camoufox remote debugging server and write its WebSocket URL to
server_url.txt.

This launcher exits immediately after the server is ready. The server keeps
running in the background, so other scripts can be run in the same terminal.
Run 00_stop_server.py when you want to close the server.
"""

import base64
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import orjson
from camoufox.server import LAUNCH_SCRIPT, get_nodejs, to_camel_case_dict
from camoufox.utils import launch_options

URL_FILE = Path(__file__).parent / "server_url.txt"
LOG_FILE = Path(__file__).parent / "camoufox_server.log"
WS_PATTERN = re.compile(r"ws://\S+")


def _remove_none(d: dict) -> dict:
    """Remove None values so Playwright launchServer does not receive JSON null."""
    return {k: v for k, v in d.items() if v is not None}


def _subprocess_kwargs() -> dict:
    """Return options that let the server process outlive this launcher."""
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def _wait_for_ws_url(process: subprocess.Popen, timeout: int = 30) -> str | None:
    """Wait until the server writes its WebSocket URL to the log file."""
    deadline = time.time() + timeout
    position = 0

    while time.time() < deadline:
        if LOG_FILE.exists():
            with LOG_FILE.open("r", encoding="utf-8", errors="replace") as log_file:
                log_file.seek(position)
                chunk = log_file.read()
                position = log_file.tell()

            match = WS_PATTERN.search(chunk)
            if match:
                return match.group()

        if process.poll() is not None:
            print("Server process exited unexpectedly.")
            return None

        time.sleep(0.2)

    return None


def main() -> None:
    print("Starting Camoufox server...")

    config = launch_options(headless=False)
    config = _remove_none(config)
    payload = base64.b64encode(orjson.dumps(to_camel_case_dict(config))).decode()

    nodejs = get_nodejs()
    with LOG_FILE.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [nodejs, str(LAUNCH_SCRIPT)],
            cwd=Path(nodejs).parent / "package",
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            **_subprocess_kwargs(),
        )

        assert process.stdin
        process.stdin.write(payload)
        process.stdin.close()

    ws_url = _wait_for_ws_url(process)
    if not ws_url:
        process.terminate()
        print(f"Timed out while waiting for WebSocket URL. See log: {LOG_FILE}")
        sys.exit(1)

    URL_FILE.write_text(ws_url, encoding="utf-8")
    print(f"Server started in the background: {ws_url}")
    print(f"Connection URL saved to: {URL_FILE}")
    print(f"Log file: {LOG_FILE}")
    print("You can run other commands now. Use 00_stop_server.py to stop the server.")


if __name__ == "__main__":
    main()
