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
```

Run the following command

```
export FLASK_ENV=development
python server.py
```
