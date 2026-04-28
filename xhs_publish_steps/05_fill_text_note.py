from common import browser_session, fill_text_note, get_publish_page


def main() -> None:
    with browser_session() as (_, context):
        page = get_publish_page(context)
        fill_text_note(page)
        print("标题和正文填写完成。脚本不会点击「发布」按钮。")


if __name__ == "__main__":
    main()
