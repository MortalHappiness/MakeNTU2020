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

# ========================================

headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
           "Content-Type": "application/json"}

with open("./richmenubody.json") as fin:
    body = json.load(fin)

res = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
                       headers=headers, data=json.dumps(body).encode('utf-8'))

if not res.ok:
    print(res.text)
    exit()

richmenu_id = json.loads(res.text)["richMenuId"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

with open("images/bottom_menu.png", 'rb') as f:
    line_bot_api.set_rich_menu_image(richmenu_id, "image/jpeg", f)

req = requests.request('POST', 'https://api.line.me/v2/bot/user/all/richmenu/'+richmenu_id, 
                       headers=headers)

print(req.text)
