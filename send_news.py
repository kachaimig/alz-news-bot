import os
import smtplib
from email.mime.text import MIMEText
import openai

# ChatGPTでニュース生成（例）
openai.api_key = os.environ["OPENAI_API_KEY"]
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "アルツハイマー病に関する最新ニュースを3件、日本語で要約してください。"}]
)
news = response.choices[0].message.content

# メール作成
from_addr = os.environ["EMAIL_ADDRESS"]
to_addrs = [addr.strip() for addr in os.environ["RECIPIENTS"].split(",")]

msg = MIMEText(news, _charset="utf-8")
msg["Subject"] = "📬 毎日の認知症ニュースまとめ"
msg["From"] = from_addr
msg["To"] = ", ".join(to_addrs)

# Gmailで送信
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(from_addr, os.environ["EMAIL_PASSWORD"])
    server.send_message(msg)
