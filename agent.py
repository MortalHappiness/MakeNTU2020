import requests

# ========================================


def update_current_people(url, store_name, secret_key, current_people):
    payload = {"store_name": store_name,
               "secret_key": secret_key,
               "current_people": current_people,
               }
    r = requests.put(url + "/api/current-people", json=payload)
    return r.ok, r.content, r.status_code


def get_max_capacity(url, store_name):
    r = requests.get(url + "/api/max-capacity?name=" + store_name)
    return r.ok, r.content, r.status_code

def get_last_num(url, store_name):
    r = requests.get(url + "/api/last-num?name=" + store_name)
    return r.ok, r.content, r.status_code

# ========================================


if __name__ == '__main__':
    print(get_max_capacity("http://localhost:8000", "邦食堂"))
    print(get_last_num("http://localhost:8000", "邦食堂"))
