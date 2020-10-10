import os
import uuid
import urllib.parse
from io import BytesIO

import qrcode
from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    abort,
    session,
    send_file,
    send_from_directory,
    redirect,
    render_template,
)
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
    CarouselTemplate,
    CarouselColumn,
    URITemplateAction,
    MessageTemplateAction,
    QuickReply,
    QuickReplyButton,
    MessageAction,
    ConfirmTemplate,
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


app = Flask(__name__, template_folder="templates")
app.secret_key = str(uuid.uuid1().hex)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

mongo_client = MongoClient(MONGO_HOST)
db = mongo_client[MONGO_DB_NAME]

# ========================================

HELP_MESSAGE = """指令教學：

「help」: 顯示教學
「#店名」：查詢店家資訊
「我要排隊：店名」：開始排隊
「吃什麼」：顯示餐廳清單

範例：
「#邦食堂」
「我要排隊：邦食堂」
「取消排隊：邦食堂」

也可以從螢幕下方的選單顯示地圖與教學～
祝您使用愉快 """

QUEUE_SEND_MESSAGE_NUM = 2

# ========================================


@app.route("/")
def index():
    return "Hi"


@app.route("/login")
def login():
    return render_template("login.html")


@app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('images', path)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


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


@app.route("/api/max-capacity")
def api_max_capacity():
    store_name = request.args.get("name", None)
    if store_name is None:
        abort(400)
    store = db.stores.find_one({"name": store_name})
    return str(store["max_capacity"])


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


@app.route("/api/qrcode", methods=["GET"])
def api_qrcode():
    data = request.args.get("data", None)
    if data is None:
        abort(400)
    pil_img = qrcode.make(data)
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


@app.route("/api/stores", methods=["GET"])
def api_stores():
    result = db.stores.aggregate(
        [
            {"$project":
                {"_id": False,
                 "name": True,
                 "latitude": True,
                 "longitude": True,
                 "max_capacity": True,
                 "current_people": True,
                 "queuing_num":
                    {"$size": "$queuing_people"}
                 }
             }
        ]
    )
    return str(list(result))


@app.route("/api/map/", methods=["GET"])
def api_map():
    return send_from_directory('map', "index.html")


@app.route("/api/map/<path:path>", methods=["GET"])
def api_map_path(path):
    return send_from_directory('map', path)


@app.route("/api/session", methods=["POST"])
def api_session():
    username = request.form.get("username", None)
    password = request.form.get("password", None)
    if username is None or password is None:
        abort(400)
    result = db.stores.find_one({"name": username, "secret_key": password})
    if result is None:
        abort(403)
    session["username"] = username
    return "Login successfully!", 200


@app.route("/api/pop-user", methods=["GET"])
def api_pop_user():
    store_name = session.get("username", None)
    if store_name is None:
        return redirect("/login")
    user_id = request.args.get("userid", None)
    is_queuing = db.stores.find_one({"name": store_name,
                                     "queuing_people.user_id": user_id},
                                    {"queuing_people.$": True}
                                    )
    if is_queuing is None:
        return "The user is not queuing now!"
    result = db.stores.aggregate([
        {"$match": {"name": store_name}},
        {"$project":
         {"matchedIndex":
          {"$indexOfArray": ["$queuing_people.user_id", user_id]}
          }
         }])
    queuing_index = list(result)[0]["matchedIndex"]
    if queuing_index != 0:
        return "The user is not line at the first!"
    store = db.stores.find_one({"name": store_name})
    db.stores.update_one({"name": store_name,
                          "queuing_people.user_id": user_id},
                         {"$pull": {"queuing_people": {"user_id": user_id}}}
                         )
    line_bot_api.push_message(
        user_id,
        TextSendMessage(
            text=f"你已成功進入店家！"))
    if len(store["queuing_people"]) > QUEUE_SEND_MESSAGE_NUM:
        line_bot_api.push_message(
            store["queuing_people"][QUEUE_SEND_MESSAGE_NUM]["user_id"],
            TextSendMessage(
                text=f"{store['name']}的排隊快輪到您了，請留意排隊進度"))

    return "Successfully pop the user!"

# ========================================


@ handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Decide what Component to return to Channel
    reply = get_reply(event.source.user_id, event.message.text)
    line_bot_api.reply_message(event.reply_token, reply)


# ========================================

QuickReply_text_message_help = TextSendMessage(
    text=HELP_MESSAGE,
    quick_reply=QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(label="#邦食堂", text="#邦食堂"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#微笑廚房", text="#微笑廚房"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#五九麵館", text="#五九麵館"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#大李水餃", text="#大李水餃"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#合益佳雞肉飯", text="#合益佳雞肉飯"),
            )
        ]))

QuickReply_text_message_nostore = TextSendMessage(
    text="抱歉，查無此店",
    quick_reply=QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(label="#邦食堂", text="#邦食堂"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#微笑廚房", text="#微笑廚房"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#五九麵館", text="#五九麵館"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#大李水餃", text="#大李水餃"),
            ),
            QuickReplyButton(
                action=MessageAction(label="#合益佳雞肉飯", text="#合益佳雞肉飯"),
            )
        ]))

QuickReply_text_message_nostore_lineup = TextSendMessage(
    text="抱歉，查無此店",
    quick_reply=QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(label="我要排隊：邦食堂", text="我要排隊：邦食堂"),
            ),
            QuickReplyButton(
                action=MessageAction(label="我要排隊：微笑廚房", text="我要排隊：微笑廚房"),
            ),
            QuickReplyButton(
                action=MessageAction(label="我要排隊：五九麵館", text="我要排隊：五九麵館"),
            ),
            QuickReplyButton(
                action=MessageAction(label="我要排隊：大李水餃", text="我要排隊：大李水餃"),
            ),
            QuickReplyButton(
                action=MessageAction(
                    label="我要排隊：合益佳雞肉飯", text="我要排隊：合益佳雞肉飯"),
            )
        ]))

QuickReply_text_message_nostore_cancel = TextSendMessage(
    text="抱歉，查無此店",
    quick_reply=QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(label="取消排隊：邦食堂", text="取消排隊：邦食堂"),
            ),
            QuickReplyButton(
                action=MessageAction(label="取消排隊：微笑廚房", text="取消排隊：微笑廚房"),
            ),
            QuickReplyButton(
                action=MessageAction(label="取消排隊：五九麵館", text="取消排隊：五九麵館"),
            ),
            QuickReplyButton(
                action=MessageAction(label="取消排隊：大李水餃", text="取消排隊：大李水餃"),
            ),
            QuickReplyButton(
                action=MessageAction(
                    label="取消排隊：合益佳雞肉飯", text="取消排隊：合益佳雞肉飯"),
            )
        ]))

Confirm_template = TemplateSendMessage(
    alt_text='目錄 template',
    template=ConfirmTemplate(
        title='確定取消？',
        text='確定要取消排隊？',
        actions=[
            MessageTemplateAction(
                label='Yes',
                text='Yes'
            ),
            MessageTemplateAction(
                label='No',
                text='No'
            )
        ])
)

# ========================================


def get_reply(user_id, text):
    """
    Given text, return reply text
    """
    text = text.strip()

    if text in ["#", "help"]:
        return QuickReply_text_message_help

    if text.startswith("#"):
        store_name = text[1:]
        store = db.stores.find_one({"name": store_name})
        if store is None:
            return QuickReply_text_message_nostore
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
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + store["image"],
                        image_aspect_ratio="square",
                        text="\n".join(
                            [f"{k}： {v}" for k, v in text_information.items()]),
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": store["fanpage"]
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
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + store["image"],
                        image_aspect_ratio="square",
                        text=f"目前已滿\n排隊人數：{len(store['queuing_people'])}",
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": store["fanpage"]
                            },
                            MessageTemplateAction(
                                label="我要排隊",
                                text=f"我要排隊：{store['name']}",
                            ),
                        ]
                    )
                )
        else:  # not is_full
            if len(store["queuing_people"])>0:
                text_information = {
                    "目前排隊編號": store["last_num"],
                }
                return TemplateSendMessage(
                    alt_text="not is_full_queuing",
                    template=ButtonsTemplate(
                        title=store_name,
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + store["image"],
                        image_aspect_ratio="square",
                        text="目前已滿\n目前排隊編號："+store["last_num"],
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": store["fanpage"]
                            },
                            MessageTemplateAction(
                                label="我要排隊",
                                text=f"我要排隊：{store['name']}",
                            ),
                        ]
                    )
                )
            else:
                store_information = {
                    "目前人數": store['current_people'],
                    "最大人數": store['max_capacity'],
                    "剩餘座位": store['max_capacity'] - store['current_people'],
                }
                return TemplateSendMessage(
                    alt_text="not is_full",
                    template=ButtonsTemplate(
                        title=store_name,
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + store["image"],
                        image_aspect_ratio="square",
                        text="\n".join(
                            [f"{k}： {v}" for k, v in store_information.items()]
                        ),
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": store["fanpage"]
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
            return QuickReply_text_message_nostore_lineup
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
        qrcode_url = (SERVER_HOST + "/api/qrcode?data=" +
                      urllib.parse.quote(SERVER_HOST + "/api/pop-user?userid=" +
                                         user_id, safe="")
                      )
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
            return QuickReply_text_message_nostore_cancel
        is_queuing = db.stores.find_one({"name": store_name,
                                         "queuing_people.user_id": user_id},
                                        {"queuing_people.$": True}
                                        )
        if is_queuing is None:
            return TextSendMessage(text=f"您沒有在排隊，故無法取消排隊")
        result = db.stores.aggregate([
            {"$match": {"name": store_name}},
            {"$project":
                {"matchedIndex":
                    {"$indexOfArray": ["$queuing_people.user_id", user_id]}
                 }
             }])
        queuing_index = list(result)[0]["matchedIndex"]
        db.stores.update_one({"name": store_name,
                              "queuing_people.user_id": user_id},
                             {"$pull": {"queuing_people": {"user_id": user_id}}}
                             )

        if (queuing_index in [0, 1] and
                len(store["queuing_people"]) > QUEUE_SEND_MESSAGE_NUM):
            line_bot_api.push_message(
                store["queuing_people"][QUEUE_SEND_MESSAGE_NUM]["user_id"],
                TextSendMessage(
                    text=f"{store['name']}的排隊快輪到您了，請留意排隊進度"))
        return TextSendMessage(text="取消排隊成功！")

    if text == "吃什麼":
        return TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + "smile.jpeg",
                        title='微笑廚房',
                        text='106台北市大安區和平東路二段118巷54弄3號',
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": "https://www.facebook.com/smileadam11"
                            },
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + "大李.jpeg",
                        title='大李水餃',
                        text='106台北市大安區和平東路二段118巷54弄35號',
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": "https://www.facebook.com/pages/%E5%A4%A7%E6%9D%8E%E6%B0%B4%E9%A4%83/177588238954445/"
                            },
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + "五九.jpg",
                        title='五九麵館',
                        text='106台北市大安區和平東路二段118巷57-1號',
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": "https://www.facebook.com/%E4%BA%94%E4%B9%9D%E9%BA%B5%E9%A4%A8-860910354254432"
                            },
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + "合益佳.jpg",
                        title='合益佳雞肉飯',
                        text='106台北市大安區和平東路二段118巷54弄7號',
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": "https://www.facebook.com/ntueater/posts/703330173174981/"
                            },
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url=SERVER_HOST +
                        "/images/" + "banshokudou.png",
                        title='邦食堂',
                        text='106台北市大安區和平東路二段96巷17弄28號',
                        actions=[
                            {
                                "type": "uri",
                                "label": "地圖",
                                "uri": SERVER_HOST + "/api/map"
                            },
                            {
                                "type": "uri",
                                "label": "Facebook",
                                "uri": "https://www.facebook.com/banfoodplace/"
                            },
                        ]
                    )
                ]
            )
        )

    return QuickReply_text_message_help

# ========================================


if __name__ == '__main__':
    app.run(port=PORT)
