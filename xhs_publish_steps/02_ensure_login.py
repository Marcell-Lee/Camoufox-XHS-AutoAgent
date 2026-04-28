from common import browser_session, ensure_login, get_publish_page


def main() -> None:
    with browser_session() as (_, context):
        page = get_publish_page(context)
        ensure_login(context, page)
        print("登录检查完成。")


if __name__ == "__main__":
    main()
