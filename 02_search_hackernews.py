"""
连接到已运行的 Camoufox 服务器，打开 Google，
在搜索框中输入 "hack news" 并执行搜索。
请先运行 01_launch_server.py，再执行本脚本。
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL_FILE = Path(__file__).parent / "server_url.txt"

SEARCH_QUERY = "hack news"


def main() -> None:
    if not URL_FILE.exists():
        raise FileNotFoundError(
            "未找到 server_url.txt，请先运行 01_launch_server.py"
        )

    ws_url = URL_FILE.read_text(encoding="utf-8").strip()
    print(f"连接到服务器: {ws_url}")

    with sync_playwright() as p:
        browser = p.firefox.connect(ws_url)
        page = browser.new_page()

        print("正在打开 Google...")
        page.goto("https://www.google.com", wait_until="domcontentloaded")

        # 点击搜索输入框（Google 首页搜索框的 name 属性为 "q"）
        print("点击搜索框...")
        search_box = page.locator('textarea[name="q"], input[name="q"]').first
        search_box.click()

        # 输入搜索关键词
        print(f'输入搜索内容: "{SEARCH_QUERY}"')
        search_box.fill(SEARCH_QUERY)

        # 按 Enter 执行搜索
        print("按下 Enter 执行搜索...")
        search_box.press("Enter")

        # 等待搜索结果加载
        page.wait_for_load_state("domcontentloaded")
        print(f"搜索完成，当前页面标题: {page.title()}")

        input("搜索结果已显示，按 Enter 键关闭页面...")
        page.close()


if __name__ == "__main__":
    main()
