import json
import time

import requests

with open("replays/04_soloq_soloq_1949947163.json", "r", encoding="utf-8") as f:
    data = json.load(f)
replay = {"replay": data}

response = requests.post(
    "http://127.0.0.1:8000/upload",
    json=replay,
    timeout=15,
)
fid = response.json()["file_id"]

while True:
    response = requests.get(f"http://127.0.0.1:8000/check/{fid}", timeout=15)
    res = response.json()
    print("ステータス:", res["status"])

    if res["status"] == "完了":
        print("結果:", res["text"])
        break
    elif res["status"] == "error":
        print("予期しないエラーが発生しました。しばらくしてから再度お試しください。")
        break

    time.sleep(3)