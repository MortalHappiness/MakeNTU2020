import requests
import json
import os

from dotenv import load_dotenv

from linebot import (
    LineBotApi, WebhookHandler
)

# ========================================

if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if LINE_CHANNEL_ACCESS_TOKEN is None:
    print('Please specify LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    exit()

SERVER_HOST = os.getenv("SERVER_HOST", None)
if SERVER_HOST is None:
    print('Please specify SERVER_HOST ' +
          'as environment variables.')
    exit()

# ========================================

headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
           "Content-Type": "application/json"}

body = {
    "size": {
        "width": 2500,
        "height": 833
    },
    "selected": False,
    "name": "richmenu-1",
    "chatBarText": "選單",
    "areas": [
        {
            "bounds": {
                "x": 0,
                "y": 0,
                "width": 1250,
                "height": 833
            },
            "action": {
                "type": "uri",
                "label": "網址",
                "uri": SERVER_HOST + "/api/map"
            }
        },
        {
            "bounds": {
                "x": 1250,
                "y": 0,
                "width": 1250,
                "height": 833
            },
            "action": {
                "type": "message",
                "label": "文字",
                "text": "Help"
            }
        }
    ]
}

res = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
                       headers=headers, data=json.dumps(body).encode('utf-8'))

if not res.ok:
    print(res.text)
    exit()

richmenu_id = json.loads(res.text)["richMenuId"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

with open("images/bottom_menu.png", 'rb') as f:
    line_bot_api.set_rich_menu_image(richmenu_id, "image/jpeg", f)

res = requests.request('POST', 'https://api.line.me/v2/bot/user/all/richmenu/' +
                       richmenu_id, headers=headers)

if not res.ok:
    print(res.text)
    exit()
