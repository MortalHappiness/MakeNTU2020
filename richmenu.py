import requests
import json

from dotenv import load_dotenv

# ========================================

if os.getenv("FLASK_ENV") != "production":
    load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if LINE_CHANNEL_ACCESS_TOKEN is None:
    print('Please specify LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    exit()

# ========================================

headers = {f"Authorization": "Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
           "Content-Type": "application/json"}

body = {
    "size": {"width": 2500, "height": 1686},
    "selected": "true",
    "name": "Controller",
    "chatBarText": "Controller",
    "areas": [
        {
            "bounds": {"x": 551, "y": 325, "width": 321, "height": 321},
            "action": {"type": "message", "text": "up"}
        },
        {
            "bounds": {"x": 876, "y": 651, "width": 321, "height": 321},
            "action": {"type": "message", "text": "right"}
        },
        {
            "bounds": {"x": 551, "y": 972, "width": 321, "height": 321},
            "action": {"type": "message", "text": "down"}
        },
        {
            "bounds": {"x": 225, "y": 651, "width": 321, "height": 321},
            "action": {"type": "message", "text": "left"}
        },
        {
            "bounds": {"x": 1433, "y": 657, "width": 367, "height": 367},
            "action": {"type": "message", "text": "btn b"}
        },
        {
            "bounds": {"x": 1907, "y": 657, "width": 367, "height": 367},
            "action": {"type": "message", "text": "btn a"}
        }
    ]
}

res = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
                       headers=headers, data=json.dumps(body).encode('utf-8'))

print(res.text)
