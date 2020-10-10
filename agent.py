import requests

# ========================================


def update_current_people(url, store_name, secret_key, current_people):
    payload = {"store_name": store_name,
               "secret_key": secret_key,
               "current_people": current_people,
               }
    r = requests.put(url + "/api/current-people", json=payload)
    return r.ok, r.content, r.status_code

# ========================================


if __name__ == '__main__':
    print(update_current_people("http://localhost:8000", "store1",
                                "store1-secret", 2))
