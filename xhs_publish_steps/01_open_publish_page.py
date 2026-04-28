from common import browser_session, get_publish_page


def main() -> None:
    with browser_session() as (_, context):
        page = get_publish_page(context)
        open_publish_page(page)
        print("发布页面已打开。")


if __name__ == "__main__":
    main()
