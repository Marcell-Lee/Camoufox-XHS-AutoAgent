from common import browser_session, fill_title, get_publish_page, select_text_note_tab


def main() -> None:
    with browser_session() as (_, context):
        page = get_publish_page(context)
        select_text_note_tab(page)
        fill_title(page)
        print("标题填写完成。")


if __name__ == "__main__":
    main()
