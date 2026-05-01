from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

URL_FILE = PROJECT_ROOT / "server_url.txt"
STATE_FILE = PROJECT_ROOT / "xhs_state.json"
SESSION_STATUS_FILE = PROJECT_ROOT / "xhs_publish_session.json"
SESSION_LOG_FILE = PROJECT_ROOT / "xhs_publish_session.log"
SESSION_COMMAND_FILE = PROJECT_ROOT / "xhs_publish_command.json"
SESSION_RESULT_FILE = PROJECT_ROOT / "xhs_publish_result.json"

PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"
XHS_DOMAIN = "xiaohongshu.com"

NOTE_TITLE = "测试标题 - 自动化测试"
NOTE_BODY = "这是一篇自动化测试笔记，仅用于流程验证，不会实际发布。"

LOGIN_URL_PARTS = ("login", "signin", "sign_in")
PUBLISH_READY_SELECTOR = (
    'input[placeholder*="标题"], textarea[placeholder*="标题"], [contenteditable][placeholder*="标题"], '
    'textarea[placeholder*="内容"], [contenteditable][placeholder*="内容"], [contenteditable][placeholder*="正文"]'
)
LOGIN_SELECTORS = (
    "text=/登录|扫码登录|手机号登录|验证码登录|密码登录/",
    'input[placeholder*="手机号"], input[placeholder*="验证码"]',
)

TITLE_SELECTOR = (
    'input[placeholder*="标题"], textarea[placeholder*="标题"], [contenteditable][placeholder*="标题"]'
)
BODY_SELECTOR = (
    'textarea[placeholder*="内容"], [contenteditable][placeholder*="内容"],'
    ' [contenteditable][placeholder*="正文"]'
)
TEXT_TAB_SELECTOR = 'div[class*="tab"]:has-text("文字"), button:has-text("文字")'
