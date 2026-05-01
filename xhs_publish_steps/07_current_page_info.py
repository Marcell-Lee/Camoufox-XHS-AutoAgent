# 从命令客户端导入 send_command，用来向后台 session_keeper 发送动作命令。
from command_client import send_command

# 从公共模块导入浏览器连接、页面查找、登录页判断、发布页就绪判断等工具函数。
from common import browser_session, get_publish_page, is_login_page, is_publish_page_ready


# 定义统一的控制台日志函数，方便观察脚本当前执行到哪一步。
def log(message: str, level: str = "INFO") -> None:
    # 打印带级别前缀的日志，例如：[INFO] 正在读取页面信息...
    print(f"[{level}] {message}")


# 定义页面信息采集函数，传入浏览器上下文 context 和当前页面 page。
def collect_page_info(context, page) -> dict:  # noqa: ANN001
    # 输出日志：开始收集页面信息。
    log("开始收集当前页面信息")

    # 创建页签列表，用来保存当前浏览器里所有打开的页面。
    pages = []

    # 遍历当前浏览器上下文中的所有页签，并带上页签序号。
    for index, item in enumerate(context.pages):
        # 判断这个页签是否已经被关闭。
        is_closed = item.is_closed()

        # 输出日志：正在读取某个页签的基础状态。
        log(f"读取页签状态：index={index}, closed={is_closed}")

        # 把页签信息加入 pages 列表。
        pages.append(
            {
                # 保存页签序号。
                "index": index,
                # 如果页签已关闭，则 URL 置空；否则读取当前 URL。
                "url": "" if is_closed else item.url,
                # 如果页签已关闭，则标题置空；否则读取当前标题。
                "title": "" if is_closed else item.title(),
                # 标记这个页签是不是当前脚本正在操作的页面。
                "is_current": item == page,
                # 保存页签是否关闭。
                "is_closed": is_closed,
            }
        )

    # 判断当前页面是否已经关闭。
    if page.is_closed():
        # 输出警告日志：当前页面已关闭。
        log("当前页面已经关闭，无法继续读取 URL、标题和正文内容", "WARN")

        # 返回一个表示页面关闭状态的数据结构。
        return {
            # 标记当前页面已关闭。
            "is_closed": True,
            # 页面已关闭时 URL 为空。
            "url": "",
            # 页面已关闭时标题为空。
            "title": "",
            # 页面已关闭时不再判断是否为登录页。
            "is_login_page": False,
            # 页面已关闭时不再判断发布页是否就绪。
            "is_publish_page_ready": False,
            # 页面已关闭时正文摘要为空。
            "text_preview": "",
            # 仍然返回已收集到的页签列表。
            "pages": pages,
        }

    # 输出日志：开始读取页面正文文本。
    log("开始读取页面 body 文本")

    # 尝试读取页面 body 的可见文本。
    try:
        # 读取 body 文本，并去掉首尾空白。
        text_preview = page.locator("body").inner_text(timeout=3000).strip()

        # 输出日志：正文读取成功。
        log(f"页面文本读取成功，字符数={len(text_preview)}")

    # 如果读取正文失败，不中断脚本，只记录空字符串。
    except Exception as exc:
        # 输出警告日志：正文读取失败。
        log(f"页面文本读取失败：{exc}", "WARN")

        # 正文读取失败时使用空字符串。
        text_preview = ""

    # 如果正文太长，截断到 1200 个字符，避免控制台输出过多。
    if len(text_preview) > 1200:
        # 输出日志：正文过长，将进行截断。
        log("页面文本超过 1200 个字符，将只输出前 1200 个字符")

        # 截断正文，并在末尾加省略号。
        text_preview = f"{text_preview[:1200]}..."

    # 输出日志：开始判断页面状态。
    log("开始判断登录页状态和发布页就绪状态")

    # 判断当前页面是否是登录页。
    login_page = is_login_page(page)

    # 判断当前页面是否是已经就绪的发布页。
    publish_page_ready = is_publish_page_ready(page)

    # 输出日志：页面状态判断完成。
    log(f"页面状态判断完成：login_page={login_page}, publish_page_ready={publish_page_ready}")

    # 返回当前页面的完整信息。
    return {
        # 标记当前页面没有关闭。
        "is_closed": False,
        # 保存当前页面 URL。
        "url": page.url,
        # 保存当前页面标题。
        "title": page.title(),
        # 保存是否为登录页。
        "is_login_page": login_page,
        # 保存发布页是否就绪。
        "is_publish_page_ready": publish_page_ready,
        # 保存页面文本摘要。
        "text_preview": text_preview,
        # 保存所有页签信息。
        "pages": pages,
    }


# 定义获取当前页面信息的入口函数。
def get_current_page_info() -> dict:
    # 输出日志：优先尝试通过后台守护进程读取页面信息。
    log("尝试通过 session_keeper 命令通道读取当前页面信息")

    # 尝试发送 current_page_info 命令给后台 session_keeper。
    try:
        # 发送命令并取出返回结果中的 data 字段。
        data = send_command("current_page_info")["data"]

        # 输出日志：命令通道读取成功。
        log("session_keeper 命令通道读取成功")

        # 返回命令通道拿到的数据。
        return data

    # 如果命令文件被占用、权限受限，或者后台进程不支持这个命令，则走兜底逻辑。
    except (OSError, RuntimeError) as exc:
        # OSError 通常是命令文件写入失败或被占用，可以直接走浏览器连接兜底。
        can_fallback = isinstance(exc, OSError)

        # RuntimeError 只有在后台不认识 current_page_info 命令时才走兜底。
        can_fallback = can_fallback or "current_page_info" in str(exc)

        # 如果当前异常不能安全兜底，说明是真实错误，继续抛出。
        if not can_fallback:
            # 输出错误日志：遇到无法兜底处理的异常。
            log(f"命令通道失败，且不是 current_page_info 兼容问题：{exc}", "ERROR")

            # 重新抛出异常，让调用者看到真实错误。
            raise

        # 输出警告日志：命令通道不可用，将直接连接浏览器。
        log(f"命令通道不可用，改为直接连接浏览器读取：{exc}", "WARN")

    # 输出日志：准备直接连接浏览器。
    log("正在直接连接当前浏览器会话")

    # 通过 browser_session 连接已有浏览器，不加载保存的登录状态，避免影响当前页面。
    with browser_session(load_saved_state=False) as (_, context):
        # 输出日志：浏览器连接成功。
        log("浏览器连接成功，开始查找当前小红书页面")

        # 查找已打开的小红书发布页；create=False 表示找不到就报错，不自动新开页面。
        page = get_publish_page(context, create=False)

        # 输出日志：已找到页面。
        log(f"已找到页面：{page.url}")

        # 采集并返回当前页面信息。
        return collect_page_info(context, page)


# 定义布尔值格式化函数，把 True/False 转成 yes/no。
def yes_no(value: bool) -> str:
    # True 返回 yes，False 返回 no，方便控制台阅读。
    return "yes" if value else "no"


# 定义脚本主函数。
def main() -> None:
    # 输出日志：脚本开始执行。
    log("07_current_page_info.py 开始执行")

    # 获取当前页面信息。
    data = get_current_page_info()

    # 输出日志：页面信息获取完成。
    log("当前页面信息获取完成，开始打印结果")

    # 打印当前页面状态分隔标题。
    print("\n=== Current Page Status ===")

    # 打印当前页面 URL。
    print(f"URL: {data.get('url', '')}")

    # 打印当前页面标题。
    print(f"Title: {data.get('title', '')}")

    # 打印当前页面是否关闭。
    print(f"Closed: {yes_no(data.get('is_closed', False))}")

    # 打印当前页面是否是登录页。
    print(f"Login page: {yes_no(data.get('is_login_page', False))}")

    # 打印当前发布页是否就绪。
    print(f"Publish page ready: {yes_no(data.get('is_publish_page_ready', False))}")

    # 打印页签列表分隔标题。
    print("\n=== Open Tabs ===")

    # 遍历并打印所有打开的页签。
    for page in data.get("pages", []):
        # 当前页签用星号标记，其它页签留空格。
        marker = "*" if page.get("is_current") else " "

        # 读取页签标题；没有标题时显示占位文本。
        title = page.get("title") or "(no title)"

        # 读取页签 URL；没有 URL 时显示占位文本。
        url = page.get("url") or "(no URL)"

        # 打印页签序号和标题。
        print(f"{marker} [{page.get('index')}] {title}")

        # 打印页签 URL。
        print(f"    {url}")

    # 打印页面文本摘要分隔标题。
    print("\n=== Page Text Preview ===")

    # 读取页面文本摘要；没有文本时显示占位文本。
    text_preview = data.get("text_preview") or "(no page text found)"

    # 打印页面文本摘要。
    print(text_preview)

    # 输出日志：脚本执行结束。
    log("07_current_page_info.py 执行结束")


# 判断当前文件是否作为脚本直接运行。
if __name__ == "__main__":
    # 如果是直接运行，则调用 main 函数。
    main()
