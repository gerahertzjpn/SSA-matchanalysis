import json
import time

import requests

with open("replays/01_league_league_16147200961505151604.json", "r", encoding="utf-8") as f:
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
    print("Статус:", res["status"])

    if res["status"] == "готово":
        print("Результат:", res["text"])
        break

    time.sleep(3)