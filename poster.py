import feedparser
import requests
import json
import re
import os

BOT_TOKEN = "8558730057:AAHoYukZxPd7mwq3kLXj4APOYY-GVQH"
CHAT_ID   = "@zakovatinfo"
FEED_URL  = "https://www.zakovat.uz/feed/"
STATE_FILE = os.path.join(os.path.dirname(__file__), "last_posted.json")


def load_last_link():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f).get("last_link")
    return None


def save_last_link(link):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_link": link}, f)


def get_image(entry):
    for media in entry.get("media_content", []):
        if media.get("url"):
            return media["url"]
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("href") or enc.get("url")
    content = ""
    if entry.get("content"):
        content = entry["content"][0].get("value", "")
    elif entry.get("summary"):
        content = entry["summary"]
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    return match.group(1) if match else None


def send(entry):
    tags = entry.get("tags", [])
    category = "#" + re.sub(r"\s+", "_", tags[0]["term"]) if tags else ""
    caption = f"{category}\n{entry.title}\n\n👉{entry.link}" if category else f"{entry.title}\n\n👉{entry.link}"

    image_url = get_image(entry)
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/"

    if image_url:
        r = requests.post(api + "sendPhoto", data={"chat_id": CHAT_ID, "photo": image_url, "caption": caption}, timeout=30)
    else:
        r = requests.post(api + "sendMessage", data={"chat_id": CHAT_ID, "text": caption}, timeout=30)

    result = r.json()
    if result.get("ok"):
        print(f"Sent: {entry.title}")
    else:
        print(f"Error: {result.get('description')}")


def main():
    last_link = load_last_link()
    feed = feedparser.parse(FEED_URL, agent="Mozilla/5.0")

    if not feed.entries:
        print("Feed empty or unreachable.")
        return

    new_entries = []
    for entry in feed.entries:
        if entry.link == last_link:
            break
        new_entries.append(entry)

    if not new_entries:
        print("No new posts.")
        return

    for entry in reversed(new_entries[:5]):
        send(entry)

    save_last_link(feed.entries[0].link)


if __name__ == "__main__":
    main()
