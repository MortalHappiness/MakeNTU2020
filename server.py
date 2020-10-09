import os

from dotenv import load_dotenv
from flask import Flask, request, abort
from pymongo import MongoClient

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ========================================

if os.getenv('FLASK_ENV') == 'development':
    load_dotenv()

PORT = os.getenv('PORT', 8000)
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

if LINE_CHANNEL_SECRET is None or LINE_CHANNEL_ACCESS_TOKEN is None:
    print('Please specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN ' +
          'as environment variables.')
    exit()

MONGO_HOST = os.getenv("MONGO_HOST", None)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", None)

if MONGO_HOST is None or MONGO_DB_NAME is None:
    print('Please specify MONGO_HOST and MONGO_DB_NAME ' +
          'as environment variables.')
    exit()

# ========================================


app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

mongo_client = MongoClient(MONGO_HOST, 27017)
db = mongo_client[MONGO_DB_NAME]

# ========================================

HELP_MESSAGE = """Welcome to LiningLine! The following is commands available:

help: display help message"""

# ========================================


@app.route("/")
def index():
    return "Hi"


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
        print("Invalid signature. " +
              "Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Decide what Component to return to Channel
    reply_text = get_reply(event.message.text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text))

# ========================================


def get_reply(text):
    """
    Given text, return reply text
    """
    text = text.strip()

    if text in ["#", "help"]:
        return HELP_MESSAGE

    if text.startswith("#"):
        store_name = text[1:]
        store = db.stores.find_one({"name": store_name}, {"_id": False})
        if store is None:
            return f'Sorry, store "{store_name}" is not in our database!'
        return str(store)

    return HELP_MESSAGE

# ========================================


if __name__ == '__main__':
    app.run(port=PORT)
