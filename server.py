import os
from io import BytesIO

import qrcode
from dotenv import load_dotenv
from flask import Flask, request, abort, send_file
from pymongo import MongoClient

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageSendMessage,
    TemplateSendMessage,
    ButtonsTemplate,
    MessageTemplateAction,
)
import qrcode

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

SERVER_HOST = os.getenv("SERVER_HOST", None)

if SERVER_HOST is None:
    print('Please specify SERVER_HOST ' +
          'as environment variables.')
    exit()

# ========================================


app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

mongo_client = MongoClient(MONGO_HOST)
db = mongo_client[MONGO_DB_NAME]

# ========================================

HELP_MESSAGE = """指令教學：

「help」: 顯示教學
「#店名」：查詢店家資訊
「我要排隊：店名」：開始排隊

範例：
「#邦食堂」
「我要排隊：邦食堂」
「取消排隊：邦食堂」

也可以從螢幕下方的選單顯示地圖與教學～
祝您使用愉快 """

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


@app.route("/api/current-people", methods=['PUT'])
def api_current_people():
    if (type(request.json) != dict):
        abort(400)
    try:
        store_name = request.json["store_name"]
        secret_key = request.json["secret_key"]
        current_people = request.json["current_people"]
    except KeyError:
        abort(400)
    if (type(store_name) != str or type(secret_key) != str or
            type(current_people) != int):
        abort(400)
    store = db.stores.find_one({"name": store_name})
    if store is None:
        return "No such store_name", 400
    if secret_key != store["secret_key"]:
        abort(403)
    if not (0 <= current_people <= store["max_capacity"]):
        return ("current_people should in the range " +
                f"[0, {store['max_capacity']}]", 400)
    db.stores.update_one({"name": store_name}, {
                         "$set": {"current_people": current_people}})
    return "", 200


@app.route("/api/qrcode/<user_id>", methods=["GET"])
def api_qrcode(user_id):
    if len(user_id) > 50:
        abort(400)
    pil_img = qrcode.make(user_id)
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')

# ========================================


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Decide what Component to return to Channel
    reply = get_reply(event.source.user_id, event.message.text)
    line_bot_api.reply_message(event.reply_token, reply)


# ========================================


def get_reply(user_id, text):
    """
    Given text, return reply text
    """
    text = text.strip()

    if text in ["#", "help"]:
        return TextSendMessage(text=HELP_MESSAGE)

    if text.startswith("#"):
        store_name = text[1:]
        store = db.stores.find_one({"name": store_name})
        if store is None:
            return TextSendMessage(text=f'抱歉，查無此店')
        assert 0 <= store["current_people"] <= store["max_capacity"]
        is_full = (store["current_people"] == store["max_capacity"])
        is_queuing = db.stores.find_one({"name": store_name,
                                         "queuing_people.user_id": user_id},
                                        {"queuing_people.$": True}
                                        )
        if is_full:
            if is_queuing is not None:
                text_information = {
                    "目前排隊編號": store["last_num"],
                    "您的編號": is_queuing["queuing_people"][0]["num"],
                }
                return TemplateSendMessage(
                    alt_text="is_full and is_queuing",
                    template=ButtonsTemplate(
                        title=store_name,
                        thumbnailImageUrl=store["image"],
                        text="\n".join(
                            [f"{k}： {v}" for k, v in text_information.items()]),
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": "https://google.com"
                            },
                            MessageTemplateAction(
                                label="取消排隊",
                                text=f"取消排隊：{store['name']}",
                            ),
                        ]
                    )
                )
            else:  # not is_queuing
                return TemplateSendMessage(
                    alt_text="is_full and not is_queuing",
                    template=ButtonsTemplate(
                        title=store_name,
                        text=f"目前已滿\n排隊人數：{len(store['queuing_people'])}",
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": "https://google.com"
                            },
                            MessageTemplateAction(
                                label="我要排隊",
                                text=f"我要排隊：{store['name']}",
                            ),
                        ]
                    )
                )
        else:  # not is_full
            store_information = {
                "目前人數": store['current_people'],
                "最大人數": store['max_capacity'],
                "剩餘座位": store['max_capacity'] - store['current_people'],
            }
            return TemplateSendMessage(
                alt_text="not is_full",
                template=ButtonsTemplate(
                    title=store_name,
                    text="\n".join(
                        [f"{k}： {v}" for k, v in store_information.items()]
                    ),
                    actions=[
                        {
                            "type": "uri",
                            "label": "地圖",
                            "uri": "https://google.com"
                        },
                    ]
                )
            )

    if text.startswith("我要排隊:") or text.startswith("我要排隊："):
        if len(text) == 5:
            return TextSendMessage(text="請輸入要排隊的店名！")
        store_name = text[5:].strip()
        store = db.stores.find_one({"name": store_name})
        if store is None:
            return TextSendMessage(text=f'抱歉，查無此店')
        is_full = (store["current_people"] == store["max_capacity"])
        is_queuing = db.stores.find_one({"name": store_name,
                                         "queuing_people.user_id": user_id},
                                        {"queuing_people.$": True}
                                        )
        if not is_full:
            return TextSendMessage(text="該店尚有空位，不需排隊")
        if is_queuing is not None:
            queue_num = is_queuing["queuing_people"][0]["num"]
            return TextSendMessage(text=f"你已經正在排隊了！你的編號是{queue_num}號")
        try:
            max_num = store["queuing_people"][-1]["num"]
        except IndexError:
            max_num = 0
        db.stores.update_one({"name": store_name},
                             {"$push": {"queuing_people": {
                                 "user_id": user_id, "num": max_num + 1}}}
                             )
        qrcode_url = SERVER_HOST + "/api/qrcode/" + user_id
        return [TextSendMessage(text=f"排隊成功！你的編號是{max_num + 1}號"),
                ImageSendMessage(original_content_url=qrcode_url,
                                 preview_image_url=qrcode_url),
                TemplateSendMessage(
                    alt_text="queuing success message",
                    template=ButtonsTemplate(
                        text=f"入店時請出示上面的QRcode",
                        actions=[
                            MessageTemplateAction(
                                label="取消排隊",
                                text=f"取消排隊：{store['name']}",
                            ),
                        ]))]
    if text.startswith("取消排隊:") or text.startswith("取消排隊："):
        if len(text) == 5:
            return TextSendMessage(text="請輸入要取消排隊的店名！")
        store_name = text[5:].strip()
        store = db.stores.find_one({"name": store_name})
        if store is None:
            return TextSendMessage(text=f'抱歉，查無此店')
        is_queuing = db.stores.find_one({"name": store_name,
                                         "queuing_people.user_id": user_id},
                                        {"queuing_people.$": True}
                                        )
        if is_queuing is None:
            return TextSendMessage(text=f"您沒有在排隊，故無法取消排隊")
        db.stores.update_one({"name": store_name,
                              "queuing_people.user_id": user_id},
                             {"$pull": {"queuing_people": {"user_id": user_id}}}
                             )
        return TextSendMessage(text="取消排隊成功！")

    return TextSendMessage(text=HELP_MESSAGE)

# ========================================


if __name__ == '__main__':
    app.run(port=PORT)
