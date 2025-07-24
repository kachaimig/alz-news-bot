import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

message = "🧠 *Slack投稿テストです* 🧠\n\nBotが正常に動作しました。"

try:
    response = client.chat_postMessage(
        channel="#general",  # ← 投稿先のチャンネル名を変えてもOKです
        text=message
    )
    print("✅ 投稿成功:", response["ts"])
except SlackApiError as e:
    print(f"❌ 投稿エラー: {e.response['error']}")
