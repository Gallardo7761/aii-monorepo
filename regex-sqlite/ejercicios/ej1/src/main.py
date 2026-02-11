import requests
import re

RSS_URL = "https://www.abc.es/rss/2.0/espana/andalucia/"
ITEM_PATTERN = r"<item>(.*?)</item>"
MONTHS = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}

def get_tag(text, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else None

def format_date(raw):
    if not raw:
        return None

    m = re.search(r"\w{3}, (\d{2}) (\w{3}) (\d{4})", raw)
    if not m:
        return None

    d, mon, y = m.groups()
    return f"{d}/{MONTHS[mon]}/{y}"

def format_item(item):
    return (
        f"Título: {item['title']}\n"
        f"Link: {item['link']}\n"
        f"Fecha: {item['date']}\n"
    )
    
def get_raw():
    rss = requests.get(RSS_URL).text
    return re.findall(ITEM_PATTERN, rss, re.DOTALL)

def get_parsed():
    parsed = []

    for item in get_raw():
        parsed.append({
            "title": get_tag(item, "title"),
            "link": get_tag(item, "link"),
            "date": format_date(get_tag(item, "pubDate")),
        })

    return parsed

def main():
    user_month = input("Type a month (MM): ")
    user_day = input("Type a day (DD): ")
    d = f"{user_day}/{user_month}"
    
    for item in get_parsed():
        if item["date"] and item["date"].startswith(d):
            print(format_item(item))
    
if __name__ == "__main__":
    main()