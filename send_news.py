import os
import smtplib
from email.message import EmailMessage
import openai

# 環境変数の読み込み（明示的なエラー出力付き）
try:
    openai_api_key = os.environ["OPENAI_API_KEY"]
except KeyError:
    raise RuntimeError("環境変数 'OPENAI_API_KEY' が設定されていません。GitHub Secrets を確認してください。")

try:
    email_address = os.environ["EMAIL_ADDRESS"]
    email_password = os.environ["EMAIL_PASSWORD"]
    recipients = os.environ["RECIPIENTS"].split(",")  # カンマ区切りで複数アドレス対応
except KeyError as e:
    raise RuntimeError(f"環境変数 '{e.args[0]}' が設定されていません。GitHub Secrets を確認してください。")

# OpenAI によるニュース生成（例として簡易プロンプト）
openai.api_key = openai_api_key
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that summarizes Alzheimer’s-related research."},
        {"role": "user", "content": "最新のアルツハイマー研究について日本語で要約してください。"}
    ],
    max_tokens=500,
    temperature=0.7,
)
news_content = response["choices"][0]["message"]["content"]

# メール作成
msg = EmailMessage()
msg["Subject"] = "アルツハイマー研究最新ニュース"
msg["From"] = email_address
msg["To"] = ", ".join(recipients)
msg.set_content(news_content)

# メール送信（Gmail の場合）
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)
    print("メール送信完了")
except Exception as e:
    raise RuntimeError(f"メール送信に失敗しました: {e}")
