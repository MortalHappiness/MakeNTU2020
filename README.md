# MakeNTU2020

## Quick Start

Install packages

```
pip install -r requirements.txt
```

Write the following content into `.env`

```
FLASK_DEBUG=1
LINE_CHANNEL_SECRET=YOUR_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN=YOUR_CHANNEL_ACCESS_TOKEN
MONGO_HOST=mongodb://localhost:27017
MONGO_DB_NAME=makentu2020
```

Setting environment variables

```
export FLASK_ENV=development
```

Reset database

```
python mongo.py
```

Enable richmenu

```
python richmenu.py
```

Start server

```
python server.py
```

Use [ngrok](https://ngrok.com/) to test our linebot

```
ngrok http 8000
```

Modify your webhook URL to `https://{YOUR_NGROK_TUNNEL_ID}.ngrok.io/callback`
