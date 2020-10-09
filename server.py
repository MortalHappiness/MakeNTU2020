import os
import sys

from dotenv import load_dotenv

from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ========================================

if os. getenv('FLASK_ENV') == 'development':
    load_dotenv()

PORT = os.getenv('PORT', 8000)
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

# ========================================


app = Flask(__name__)

if LINE_CHANNEL_SECRET is None or LINE_CHANNEL_ACCESS_TOKEN is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN ' +
          'as environment variables.')
    sys.exit(1)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ========================================


@app.route("/")
def index():
    return "Hii"


@app.route("/callback", methods=['POST'])
def callback():
    """
    Webhook callback endpoint
    """
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    print(signature)

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature." +
              "Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Decide what Component to return to Channel
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == '__main__':
    app.run(port=PORT)
