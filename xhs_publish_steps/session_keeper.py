import json
import time

from common import (
    browser_session,
    fill_body,
    fill_text_note,
    fill_title,
    get_publish_page,
    is_publish_page_ready,
    is_login_page,
    open_publish_page,
    save_state,
    select_text_note_tab,
)
from config import SESSION_COMMAND_FILE, SESSION_RESULT_FILE, SESSION_STATUS_FILE


def write_status(status: str, page_url: str = "", message: str = "") -> None:
    payload = {
        "status": status,
        "page_url": page_url,
        "message": message,
        "updated_at": time.time(),
    }
    SESSION_STATUS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_result(command: dict, ok: bool, message: str = "", data: dict | None = None) -> None:
    payload = {
        "id": command.get("id"),
        "action": command.get("action"),
        "ok": ok,
        "message": message,
        "data": data or {},
        "updated_at": time.time(),
    }
    SESSION_RESULT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_command(last_id: str | None) -> dict | None:
    try:
        command = json.loads(SESSION_COMMAND_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    if not command.get("id") or command.get("id") == last_id:
        return None

    return command


def verify_login_state(context, page, timeout: int = 120) -> tuple[bool, str]:  # noqa: ANN001
    deadline = time.time() + timeout

    while time.time() < deadline:
        if page.is_closed():
            return False, "页面已经被关闭，请重新运行 01_open_publish_page.py。"

        if not is_login_page(page):
            save_state(context)
            return True, "登录检查完成"

        time.sleep(2)

    return False, f"仍未检测到登录成功，当前 URL: {page.url}"


def get_current_page_info(context, page) -> dict:  # noqa: ANN001
    pages = []
    for index, item in enumerate(context.pages):
        is_closed = item.is_closed()
        pages.append(
            {
                "index": index,
                "url": "" if is_closed else item.url,
                "title": "" if is_closed else item.title(),
                "is_current": item == page,
                "is_closed": is_closed,
            }
        )

    if page.is_closed():
        return {
            "is_closed": True,
            "url": "",
            "title": "",
            "is_login_page": False,
            "is_publish_page_ready": False,
            "text_preview": "",
            "pages": pages,
        }

    try:
        text_preview = page.locator("body").inner_text(timeout=3000).strip()
    except Exception:
        text_preview = ""

    if len(text_preview) > 1200:
        text_preview = f"{text_preview[:1200]}..."

    return {
        "is_closed": False,
        "url": page.url,
        "title": page.title(),
        "is_login_page": is_login_page(page),
        "is_publish_page_ready": is_publish_page_ready(page),
        "text_preview": text_preview,
        "pages": pages,
    }


def handle_command(command: dict, context, page) -> bool:  # noqa: ANN001
    action = command.get("action")

    if action == "current_page_info":
        data = get_current_page_info(context, page)
        write_result(command, True, "current page info collected", data)
        return False

    if action == "check_login":
        ready = is_publish_page_ready(page)
        login = is_login_page(page)
        if ready and not login:
            write_result(command, True, "当前登录态有效", {"login_required": False, "url": page.url})
        else:
            write_result(command, True, "需要手动登录", {"login_required": True, "url": page.url})
        return False

    if action == "verify_login":
        ok, message = verify_login_state(context, page)
        write_result(command, ok, message, {"url": page.url if not page.is_closed() else ""})
        return False

    if action == "fill_title":
        select_text_note_tab(page)
        fill_title(page)
        write_result(command, True, "标题填写完成", {"url": page.url})
        return False

    if action == "fill_body":
        select_text_note_tab(page)
        fill_body(page)
        write_result(command, True, "正文填写完成", {"url": page.url})
        return False

    if action == "fill_text_note":
        fill_text_note(page)
        write_result(command, True, "标题和正文填写完成", {"url": page.url})
        return False

    if action == "close_page":
        page.close()
        write_result(command, True, "页面已关闭")
        return True

    write_result(command, False, f"未知命令: {action}")
    return False


def main() -> None:
    try:
        with browser_session() as (_, context):
            page = get_publish_page(context)
            write_status("ready", page.url, "publish page is open")
            print(f"发布页面已打开并保持连接: {page.url}", flush=True)

            last_command_id = None
            while True:
                if page.is_closed():
                    write_status("closed", "", "publish page was closed")
                    break

                command = read_command(last_command_id)
                if command:
                    last_command_id = command["id"]
                    should_stop = handle_command(command, context, page)
                    if should_stop:
                        write_status("closed", "", "publish page was closed")
                        break

                time.sleep(1)
    except Exception as exc:
        write_status("error", "", str(exc))
        raise


if __name__ == "__main__":
    main()
