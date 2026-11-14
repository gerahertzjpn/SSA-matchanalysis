from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from main import main, queue

app = FastAPI()

class Bunseki(BaseModel):
    replay: dict


@app.post("/upload")
def recieve(document: Bunseki, background_tasks: BackgroundTasks):
    fid = len(queue) + 1
    print("リクエストを受信しました！")
    queue[fid] = {}
    queue[fid]["replay"] = document.replay
    queue[fid]["result"] = {"status": "分析中", "text": ""}
    background_tasks.add_task(main, fid, queue[fid]["replay"])
    return {"file_id": fid}

@app.get("/check/{fid}")
def checker(fid: int):
    if fid not in queue:
        raise HTTPException(status_code=404, detail="指定されたタスクは存在しません")
    return queue[fid]["result"]