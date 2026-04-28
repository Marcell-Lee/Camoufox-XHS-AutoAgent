from common import browser_session


def main() -> None:
    closed = 0
    with browser_session(load_saved_state=False) as (_, context):
        for page in list(context.pages):
            if "xiaohongshu.com" in page.url:
                page.close()
                closed += 1

    print(f"已关闭 {closed} 个小红书页面。")


if __name__ == "__main__":
    main()
