"""
Run the full Xiaohongshu publish test flow.

The same flow is also split into step scripts under xhs_publish_steps/ so each
operation can be executed independently.
"""

from xhs_publish_steps.common import (
    browser_session,
    ensure_login,
    fill_text_note,
    get_publish_page,
)


def main() -> None:
    with browser_session() as (_, context):
        page = get_publish_page(context)
        ensure_login(context, page)
        fill_text_note(page)

        print("\n流程测试完成。请在浏览器中核查填写结果。")
        print("注意：脚本不会点击「发布」按钮，请手动确认后继续。")


if __name__ == "__main__":
    main()
