import os
from datetime import datetime, timedelta
import feedparser
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ==== 環境変数 ====
SLACK_CHANNEL = "#alz-news-bot"
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# ==== 初期設定 ====
openai.api_key = OPENAI_API_KEY
client = WebClient(token=SLACK_BOT_TOKEN)
today = datetime.utcnow()
seven_days_ago = today - timedelta(days=7)

KEYWORDS = [
    "アルツハイマー", "認知症", "レヴィ小体", "アミロイド", "リン酸化タウ", "MCI", "軽度認知障害",
    "認知機能", "長谷川式", "神経心理検査", "alzheimer", "dementia", "経路統合能", "path integration"
]

def contains_keyword(text):
    if not text:
        return False
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False

def is_english(text):
    try:
        return text and all(ord(c) < 128 or c.isspace() for c in text[:50])
    except:
        return False

# ==== 最新のOpenAIライブラリ対応に書き換えた翻訳関数 ====
def translate_title(text):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate the following news headline into natural Japanese."},
                {"role": "user", "content": text}
            ],
            max_tokens=60
        )
        translation = response.choices[0].message.content.strip()
        print(f"翻訳成功: {text} -> {translation}")
        return translation
    except Exception as e:
        print(f"翻訳失敗エラー詳細: {e}")
        return "（翻訳失敗）"

def get_recent_articles():
    articles = []
    seen_urls = set()
    for site, url in {
        "Alzforum": "https://www.alzforum.org/rss/feed",
        "EurekAlert - Neuroscience": "https://www.eurekalert.org/rss/neuroscience.xml",
        "ScienceDaily - Alzheimer": "https://www.sciencedaily.com/rss/health_medicine/alzheimers.xml",
        "NIH News Releases": "https://www.nih.gov/news-events/news-releases/rss.xml",
        "Alzheimer's Association": "https://www.alz.org/news/feed",
        "Medical Xpress - Alzheimer": "https://medicalxpress.com/rss-feed/alzheimer-dementia-news/",
        "Neuroscience News": "https://neurosciencenews.com/feed/",
        "The Guardian - Neuroscience": "https://www.theguardian.com/science/neuroscience/rss",
        "Nature News": "https://www.nature.com/subjects/neuroscience.rss",
        "GIGAZINE": "https://gigazine.net/news/rss_2.0/",
        "ナゾロジー": "https://nazology.net/feed",
        "ITmedia NEWS": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",
        "lab-brain": "https://lab-brain.com/feed/",
        "よろず〜ニュース": "https://yorozoonews.jp/rss",
        "DIME": "https://dime.jp/feed/"
    }.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                summary = entry.get("summary", "")
                pub_date = entry.get("published_parsed") or entry.get("updated_parsed")
                if not pub_date:
                    continue
                pub_date_dt = datetime(*pub_date[:6])
                if pub_date_dt < seven_days_ago:
                    continue
                if link in seen_urls:
                    continue
                if not (contains_keyword(title) or contains_keyword(summary)):
                    continue
                seen_urls.add(link)
                articles.append({
                    "site": site,
                    "title": title,
                    "link": link,
                    "date": pub_date_dt.strftime("%Y-%m-%d")
                })
        except Exception:
            continue
    return sorted(articles, key=lambda x: x["date"], reverse=True)[:10]

def format_articles_for_slack(articles):
    message_lines = []
    for art in articles:
        line = f"🔹 [{art['site']}]｜{art['date']}\n{art['title']}"
        if is_english(art["title"]):
            ja_title = translate_title(art["title"])
            line += f"\n（{ja_title}）"
        line += f"\n{art['link']}\n"
        message_lines.append(line)
    return "\n".join(message_lines)

def post_to_slack(message):
    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        print("✅ 投稿成功")
    except Exception as e:
        print(f"❌ 投稿エラー: {e}")

if __name__ == "__main__":
    articles = get_recent_articles()
    if not articles:
        post_to_slack("🧠 過去7日以内の新着記事は見つかりませんでした。")
    else:
        message = format_articles_for_slack(articles)
        post_to_slack(message)
