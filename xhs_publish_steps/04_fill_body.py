from common import browser_session, fill_body, get_publish_page, select_text_note_tab


def main() -> None:
    with browser_session() as (_, context):
        page = get_publish_page(context)
        select_text_note_tab(page)
        fill_body(page)
        print("正文填写完成。")


if __name__ == "__main__":
    main()
