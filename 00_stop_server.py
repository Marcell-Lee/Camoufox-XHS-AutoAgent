"""
连接到已运行的 Camoufox 服务器并将其关闭。
运行后 server_url.txt 会被自动清理。
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL_FILE = Path(__file__).parent / "server_url.txt"


def main() -> None:
    if not URL_FILE.exists():
        print("server_url.txt 不存在，服务器可能已经停止。")
        return

    ws_url = URL_FILE.read_text(encoding="utf-8").strip()
    print(f"连接到服务器: {ws_url}")

    with sync_playwright() as p:
        browser = p.firefox.connect(ws_url)
        browser.close()

    URL_FILE.unlink(missing_ok=True)
    print("服务器已关闭，server_url.txt 已清理。")


if __name__ == "__main__":
    main()
