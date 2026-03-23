from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def tg_request(method, payload):
    url = f"{BASE_URL}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


def send_message(chat_id, text):
    return tg_request("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })


def send_chat_action(chat_id):
    tg_request("sendChatAction", {"chat_id": chat_id, "action": "upload_video"})


def send_video(chat_id, video_url, caption):
    return tg_request("sendVideo", {
        "chat_id": chat_id,
        "video": video_url,
        "caption": caption,
        "parse_mode": "HTML",
        "supports_streaming": True,
    })


def send_photo(chat_id, file_id, caption):
    return tg_request("sendPhoto", {
        "chat_id": chat_id,
        "photo": file_id,
        "caption": caption,
        "parse_mode": "HTML",
    })


def get_bot_info():
    return tg_request("getMe", {})


def get_user_profile_photos(user_id):
    return tg_request("getUserProfilePhotos", {"user_id": user_id, "limit": 1})


def fetch_download_url(tiktok_url):
    # Using tikwm.com - free, no API key needed
    api_url = "https://www.tikwm.com/api/"
    data = urllib.parse.urlencode({"url": tiktok_url, "hd": 1}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            if result.get("code") == 0:
                video_data = result.get("data", {})
                # Try HD first, then normal
                return video_data.get("hdplay") or video_data.get("play")
            return None
    except Exception:
        return None


def is_tiktok_url(text):
    return any(d in text.lower() for d in ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com"))


def start_message(first_name, bot_name):
    return (
        f"👋 <b>Hey {first_name}!</b> Welcome to <b>{bot_name}</b> 🎉\n\n"
        f"🎬 I can download any <b>TikTok video</b> for you — watermark-free and fast!\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>📌 How to use:</b>\n"
        f"Just send me any TikTok link and I'll handle the rest 🚀\n\n"
        f"<b>Example:</b>\n"
        f"<code>https://www.tiktok.com/@user/video/123456789</code>\n"
        f"<code>https://vm.tiktok.com/XXXXXXX/</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🛠 <b>Created by</b> <a href='https://t.me/umarj_1'>@umarj_1</a>"
    )


def downloading_message():
    return (
        "⏳ <b>Processing your TikTok...</b>\n\n"
        "🔍 Fetching video    ✅\n"
        "🎞 Processing         ⏳\n"
        "📤 Uploading          🕐\n\n"
        "<i>Just a moment...</i>"
    )


def success_message(first_name):
    return (
        f"✅ <b>Done, {first_name}!</b> Enjoy your video 🎬\n\n"
        f"🚫💧 No watermark • Downloaded & ready\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📎 Send another TikTok link anytime!\n\n"
        f"🛠 <b>Bot by</b> <a href='https://t.me/umarj_1'>@umarj_1</a>"
    )


def error_message():
    return (
        "❌ <b>Download failed!</b>\n\n"
        "<b>Possible reasons:</b>\n"
        "• Link is private, expired or deleted\n"
        "• TikTok is rate-limiting right now\n"
        "• Invalid URL format\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔁 Try again with a different link.\n"
        "💬 Help: <a href='https://t.me/umarj_1'>@umarj_1</a>"
    )


def not_a_link_message():
    return (
        "🤔 <b>That doesn't look like a TikTok link.</b>\n\n"
        "Send a link like:\n"
        "<code>https://www.tiktok.com/@user/video/123</code>\n"
        "or:\n"
        "<code>https://vm.tiktok.com/XXXXXXX/</code>\n\n"
        "🛠 <b>Bot by</b> <a href='https://t.me/umarj_1'>@umarj_1</a>"
    )


def handle_update(update):
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()
    user = message.get("from", {})
    first_name = user.get("first_name", "there")

    if not text:
        return

    if text.startswith("/start"):
        bot_info = get_bot_info()
        result = bot_info.get("result", {})
        bot_name = result.get("first_name", "TikTok Downloader Bot")
        bot_id = result.get("id", 0)
        caption = start_message(first_name, bot_name)
        photos_resp = get_user_profile_photos(bot_id)
        photos = photos_resp.get("result", {}).get("photos", [])
        if photos:
            file_id = photos[0][-1]["file_id"]
            r = send_photo(chat_id, file_id, caption)
            if not r.get("ok"):
                send_message(chat_id, caption)
        else:
            send_message(chat_id, caption)
        return

    if is_tiktok_url(text):
        send_message(chat_id, downloading_message())
        send_chat_action(chat_id)
        video_url = fetch_download_url(text)
        if video_url:
            send_chat_action(chat_id)
            r = send_video(chat_id, video_url, success_message(first_name))
            if not r.get("ok"):
                send_message(
                    chat_id,
                    f"{success_message(first_name)}\n\n"
                    f"🔗 <a href='{video_url}'>Tap here to download</a>"
                )
        else:
            send_message(chat_id, error_message())
        return

    send_message(chat_id, not_a_link_message())


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "TikTok Bot is live! 🚀"}).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            update = json.loads(body)
            handle_update(update)
        except Exception:
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def log_message(self, format, *args):
        pass
