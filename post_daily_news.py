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

# ==== ニュースフィード（RSS）一覧 ====
RSS_FEEDS = {
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
}

# ==== 英語判定用（簡易） ====
def is_english(text):
    try:
        return text and all(ord(c) < 128 or c.isspace() for c in text[:50])
    except:
        return False

# ==== 翻訳関数（OpenAI使用） ====
def translate(title_en):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"次の英語のニュース記事タイトルを自然な日本語に翻訳してください：\n{title_en}"}],
            max_tokens=100
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception:
        return "（翻訳失敗）"

# ==== フィードから記事を取得 ====
def get_recent_articles():
    articles = []
    seen_urls = set()
    for site, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                pub_date = entry.get("published_parsed") or entry.get("updated_parsed")
                if not pub_date:
                    continue
                pub_date_dt = datetime(*pub_date[:6])
                if pub_date_dt < seven_days_ago:
                    continue
                if link in seen_urls:
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

# ==== Slack投稿用メッセージ作成 ====
def format_articles_for_slack(articles):
    message_lines = []
    for art in articles:
        line = f"🔹 [{art['site']}]｜{art['date']}\n{art['title']}"
        if is_english(art["title"]):
            ja_title = translate(art["title"])
            line += f"\n（{ja_title}）"
        line += f"\n{art['link']}\n"
        message_lines.append(line)
    return "\n".join(message_lines)

# ==== Slackへ送信 ====
def post_to_slack(message):
    try:
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        print("✅ 投稿成功")
    except Exception as e:
        print(f"❌ 投稿エラー: {e}")

# ==== メイン実行 ====
if __name__ == "__main__":
    articles = get_recent_articles()
    if not articles:
        post_to_slack("🧠 過去7日以内の新着記事は見つかりませんでした。")
    else:
        message = format_articles_for_slack(articles)
        post_to_slack(message)
