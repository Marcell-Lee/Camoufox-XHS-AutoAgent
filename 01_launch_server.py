"""
启动 Camoufox 远程调试服务器，并将 WebSocket 连接地址写入 server_url.txt。
运行后保持阻塞，直到手动 Ctrl+C 停止。

修复说明：camoufox 原版 launch_server() 将 proxy=None 序列化为 JSON null，
但 Playwright 的 launchServer 不接受 null proxy，故此处手动过滤 None 值。
"""

import base64
import re
import signal
import subprocess
import sys
from pathlib import Path
from threading import Thread

import orjson
from camoufox.server import LAUNCH_SCRIPT, get_nodejs, to_camel_case_dict
from camoufox.utils import launch_options

URL_FILE = Path(__file__).parent / "server_url.txt"
WS_PATTERN = re.compile(r"ws://\S+")


def _remove_none(d: dict) -> dict:
    """递归去除值为 None 的键，避免 JSON null 传入 Playwright launchServer。"""
    return {k: v for k, v in d.items() if v is not None}


def _pipe_and_capture(stream, prefix: str, result: list) -> None:
    """把子进程输出流打印到控制台，同时捕获 WebSocket URL。"""
    for raw in stream:
        line = raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace")
        print(prefix + line, end="")
        if not result:
            match = WS_PATTERN.search(line)
            if match:
                result.append(match.group())


def main() -> None:
    print("正在启动 Camoufox 服务器...")

    # 生成启动配置并过滤 None，防止 proxy:null 报错
    config = launch_options(headless=False)
    config = _remove_none(config)
    payload = base64.b64encode(orjson.dumps(to_camel_case_dict(config))).decode()

    nodejs = get_nodejs()
    process = subprocess.Popen(
        [nodejs, str(LAUNCH_SCRIPT)],
        cwd=Path(nodejs).parent / "package",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert process.stdin
    process.stdin.write(payload)
    process.stdin.close()

    ws_result: list[str] = []

    # 分别用线程读取 stdout / stderr，避免死锁
    t_out = Thread(target=_pipe_and_capture, args=(process.stdout, "", ws_result), daemon=True)
    t_err = Thread(target=_pipe_and_capture, args=(process.stderr, "[ERR] ", []), daemon=True)
    t_out.start()
    t_err.start()

    # 等待 WS URL 出现（最多 30 秒）
    import time
    deadline = time.time() + 30
    while not ws_result and time.time() < deadline:
        if process.poll() is not None:
            print("服务器进程意外退出")
            sys.exit(1)
        time.sleep(0.2)

    if not ws_result:
        process.terminate()
        print("超时：未能获取 WebSocket 地址")
        sys.exit(1)

    ws_url = ws_result[0]
    URL_FILE.write_text(ws_url, encoding="utf-8")
    print(f"\n服务器已启动: {ws_url}")
    print(f"连接地址已保存至: {URL_FILE}")
    print("按 Ctrl+C 停止服务器\n")

    def _shutdown(sig, frame):  # noqa: ANN001
        print("\n正在关闭服务器...")
        process.terminate()
        URL_FILE.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    process.wait()
    URL_FILE.unlink(missing_ok=True)
    print("服务器已停止")


if __name__ == "__main__":
    main()
