"""
连接到已运行的 Camoufox 服务器，打开小红书创作者平台发布页面，
并执行测试发布流程（填写标题、正文，不实际提交）。

登录态持久化：
- 首次运行若未登录，脚本会暂停等待手动登录，登录成功后自动保存
  cookies 和 localStorage 到 xhs_state.json。
- 后续运行自动加载该文件，无需再次登录。

请先运行 01_launch_server.py，再执行本脚本。
"""

import json
import time
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

URL_FILE = Path(__file__).parent / "server_url.txt"
STATE_FILE = Path(__file__).parent / "xhs_state.json"

PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"
XHS_DOMAIN = "xiaohongshu.com"

NOTE_TITLE = "测试标题 - 自动化测试"
NOTE_BODY = "这是一篇自动化测试笔记，仅用于流程验证，不会实际发布。"

LOGIN_URL_PARTS = ("login", "signin", "sign_in")
PUBLISH_READY_SELECTOR = (
    'input[placeholder*="标题"], textarea[placeholder*="标题"], [contenteditable][placeholder*="标题"], '
    'textarea[placeholder*="内容"], [contenteditable][placeholder*="内容"], [contenteditable][placeholder*="正文"]'
)
LOGIN_SELECTORS = (
    "text=/登录|扫码登录|手机号登录|验证码登录|密码登录/",
    'input[placeholder*="手机号"], input[placeholder*="验证码"]',
)


def _is_login_page(page: Page) -> bool:
    url = page.url.lower()
    if any(part in url for part in LOGIN_URL_PARTS):
        return True

    if _is_publish_page_ready(page):
        return False

    return any(_is_visible(page, selector, timeout=1500) for selector in LOGIN_SELECTORS)


def _is_visible(page: Page, selector: str, timeout: int = 3000) -> bool:
    try:
        page.locator(selector).first.wait_for(state="visible", timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def _is_publish_page_ready(page: Page) -> bool:
    return _is_visible(page, PUBLISH_READY_SELECTOR, timeout=5000)


def _has_saved_login_state() -> bool:
    if not STATE_FILE.exists():
        print(f"未找到本地登录态文件: {STATE_FILE.name}")
        return False

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"⚠ {STATE_FILE.name} 不是有效 JSON，将重新登录。")
        return False

    now = time.time()
    for cookie in state.get("cookies", []):
        domain = cookie.get("domain", "")
        expires = cookie.get("expires", -1)
        if XHS_DOMAIN in domain and (expires == -1 or expires > now):
            return True

    print(f"⚠ {STATE_FILE.name} 中没有可用的小红书 cookie，将重新登录。")
    return False


def _save_state(context: BrowserContext) -> None:
    state = context.storage_state()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 登录态已保存至: {STATE_FILE}")


def _load_state(context: BrowserContext) -> None:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    # 恢复 cookies
    cookies = state.get("cookies", [])
    if cookies:
        context.add_cookies(cookies)
    # 恢复 localStorage（逐域名注入）
    origins = state.get("origins", [])
    if origins:
        page = context.new_page()
        for origin in origins:
            entries = origin.get("localStorage", [])
            if not entries:
                continue
            try:
                page.goto(origin["origin"], wait_until="domcontentloaded", timeout=8000)
                for item in entries:
                    page.evaluate(
                        "([k, v]) => localStorage.setItem(k, v)",
                        [item["name"], item["value"]],
                    )
            except Exception:
                pass
        page.close()
    print(f"✓ 已从 {STATE_FILE.name} 恢复登录态")


def fill_text_note(page: Page) -> None:
    """尝试填写图文笔记的标题和正文。"""
    text_tab = page.locator('div[class*="tab"]:has-text("文字"), button:has-text("文字")')
    if text_tab.count() > 0:
        print("点击「文字」Tab...")
        text_tab.first.click()
        page.wait_for_timeout(1000)

    title_sel = 'input[placeholder*="标题"], textarea[placeholder*="标题"], [contenteditable][placeholder*="标题"]'
    if page.locator(title_sel).count() > 0:
        print(f"填写标题: {NOTE_TITLE!r}")
        page.locator(title_sel).first.click()
        page.locator(title_sel).first.fill(NOTE_TITLE)
    else:
        print("⚠ 未找到标题输入框，跳过")

    body_sel = (
        'textarea[placeholder*="内容"], [contenteditable][placeholder*="内容"],'
        ' [contenteditable][placeholder*="正文"]'
    )
    if page.locator(body_sel).count() > 0:
        print(f"填写正文: {NOTE_BODY!r}")
        page.locator(body_sel).first.click()
        page.locator(body_sel).first.fill(NOTE_BODY)
    else:
        print("⚠ 未找到正文输入框，跳过")


def main() -> None:
    if not URL_FILE.exists():
        raise FileNotFoundError("未找到 server_url.txt，请先运行 01_launch_server.py")

    ws_url = URL_FILE.read_text(encoding="utf-8").strip()
    print(f"连接到服务器: {ws_url}")

    with sync_playwright() as p:
        browser = p.firefox.connect(ws_url)
        context = browser.new_context()

        # 有已保存的登录态则先恢复
        has_saved_state = _has_saved_login_state()
        if has_saved_state:
            try:
                _load_state(context)
            except Exception as exc:
                print(f"⚠ 恢复登录态失败，将重新登录: {exc}")
                has_saved_state = False

        page = context.new_page()

        print(f"正在打开小红书发布页面: {PUBLISH_URL}")
        page.goto(PUBLISH_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        cookie_valid = _is_publish_page_ready(page) and not _is_login_page(page)
        if has_saved_state and cookie_valid:
            print("✓ 已验证本地登录态有效")

        # 本地无登录态，或登录态已失效，则暂停等待手动操作
        if not cookie_valid:
            if has_saved_state:
                print("\n⚠ 本地登录态已加载，但验证失败，可能是 cookie 过期或账号需要重新登录。")
            else:
                print("\n⚠ 本地没有可用登录态，请在浏览器中手动完成登录。")
            input("登录完成后按 Enter 继续...")
            page.goto(PUBLISH_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            if _is_login_page(page) or not _is_publish_page_ready(page):
                print("仍在登录页，请检查登录是否成功后重新运行。")
                page.close()
                context.close()
                return

            # 登录成功，保存登录态
            _save_state(context)

        print(f"当前 URL: {page.url}")
        print(f"当前页面标题: {page.title()}")

        fill_text_note(page)

        print("\n流程测试完成。请在浏览器中核查填写结果。")
        print("注意：脚本不会点击「发布」按钮，请手动确认后继续。")
        input("按 Enter 键关闭页面并退出...")

        page.close()
        context.close()
        print("页面已关闭。")


if __name__ == "__main__":
    main()
