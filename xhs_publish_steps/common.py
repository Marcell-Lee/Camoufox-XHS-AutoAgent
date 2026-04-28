import json
import time
from contextlib import contextmanager

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

try:
    from .config import (
        BODY_SELECTOR,
        LOGIN_SELECTORS,
        LOGIN_URL_PARTS,
        NOTE_BODY,
        NOTE_TITLE,
        PUBLISH_READY_SELECTOR,
        PUBLISH_URL,
        STATE_FILE,
        TEXT_TAB_SELECTOR,
        TITLE_SELECTOR,
        URL_FILE,
        XHS_DOMAIN,
    )
except ImportError:
    from config import (
        BODY_SELECTOR,
        LOGIN_SELECTORS,
        LOGIN_URL_PARTS,
        NOTE_BODY,
        NOTE_TITLE,
        PUBLISH_READY_SELECTOR,
        PUBLISH_URL,
        STATE_FILE,
        TEXT_TAB_SELECTOR,
        TITLE_SELECTOR,
        URL_FILE,
        XHS_DOMAIN,
    )


@contextmanager
def browser_session(load_saved_state: bool = True):
    if not URL_FILE.exists():
        raise FileNotFoundError("未找到 server_url.txt，请先运行 01_launch_server.py")

    ws_url = URL_FILE.read_text(encoding="utf-8").strip()
    print(f"连接到服务器: {ws_url}")

    with sync_playwright() as p:
        browser = p.firefox.connect(ws_url)
        context = get_or_create_context(browser)
        if load_saved_state and has_saved_login_state():
            try:
                load_state(context)
            except Exception as exc:
                print(f"⚠ 恢复登录态失败，将继续使用当前浏览器状态: {exc}")

        yield browser, context


def get_or_create_context(browser: Browser) -> BrowserContext:
    if browser.contexts:
        return browser.contexts[0]
    return browser.new_context()


def get_publish_page(context: BrowserContext, create: bool = True) -> Page:
    for page in context.pages:
        if "creator.xiaohongshu.com" in page.url or "xiaohongshu.com" in page.url:
            return page

    if not create:
        raise RuntimeError("未找到已打开的小红书页面，请先运行 xhs_publish_steps/01_open_publish_page.py")

    page = context.new_page()
    open_publish_page(page)
    return page


def open_publish_page(page: Page) -> None:
    print(f"正在打开小红书发布页面: {PUBLISH_URL}")
    page.goto(PUBLISH_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    print(f"当前 URL: {page.url}")
    print(f"当前页面标题: {page.title()}")


def is_visible(page: Page, selector: str, timeout: int = 3000) -> bool:
    try:
        page.locator(selector).first.wait_for(state="visible", timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def is_publish_page_ready(page: Page) -> bool:
    return is_visible(page, PUBLISH_READY_SELECTOR, timeout=5000)


def is_login_page(page: Page) -> bool:
    url = page.url.lower()
    if any(part in url for part in LOGIN_URL_PARTS):
        return True

    if is_publish_page_ready(page):
        return False

    return any(is_visible(page, selector, timeout=1500) for selector in LOGIN_SELECTORS)


def has_saved_login_state() -> bool:
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


def save_state(context: BrowserContext) -> None:
    state = context.storage_state()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 登录态已保存至: {STATE_FILE}")


def load_state(context: BrowserContext) -> None:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    cookies = state.get("cookies", [])
    if cookies:
        context.add_cookies(cookies)

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


def ensure_login(context: BrowserContext, page: Page) -> None:
    cookie_valid = is_publish_page_ready(page) and not is_login_page(page)
    if cookie_valid:
        print("✓ 当前登录态有效")
        return

    print("\n⚠ 当前未登录或登录态失效，请在浏览器中手动完成登录。")
    input("登录完成后按 Enter 继续...")
    open_publish_page(page)

    if is_login_page(page) or not is_publish_page_ready(page):
        raise RuntimeError("仍在登录页，请检查登录是否成功后重新运行。")

    save_state(context)


def select_text_note_tab(page: Page) -> None:
    text_tab = page.locator(TEXT_TAB_SELECTOR)
    if text_tab.count() > 0:
        print("点击「文字」Tab...")
        text_tab.first.click()
        page.wait_for_timeout(1000)


def fill_title(page: Page, title: str = NOTE_TITLE) -> None:
    title_input = page.locator(TITLE_SELECTOR)
    if title_input.count() == 0:
        print("⚠ 未找到标题输入框，跳过")
        return

    print(f"填写标题: {title!r}")
    title_input.first.click()
    title_input.first.fill(title)


def fill_body(page: Page, body: str = NOTE_BODY) -> None:
    body_input = page.locator(BODY_SELECTOR)
    if body_input.count() == 0:
        print("⚠ 未找到正文输入框，跳过")
        return

    print(f"填写正文: {body!r}")
    body_input.first.click()
    body_input.first.fill(body)


def fill_text_note(page: Page) -> None:
    select_text_note_tab(page)
    fill_title(page)
    fill_body(page)
