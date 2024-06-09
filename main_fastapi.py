from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Union
from pathlib import Path
import requests
import uvicorn

f_app = FastAPI()

DOWNLOAD_URL = "https://simurg.space/gen_file?data=obs&date="

class DownloadRequest(BaseModel):
    filename: str
    local_file: Union[str, Path]

def load_data(filename: str, local_file: Union[str, Path]):
    url = DOWNLOAD_URL + filename
    max_load_per = 100
    try:
        with open(local_file, "wb") as f:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                response.raise_for_status()
            total_length = response.headers.get("content-length")

            if total_length is None:
                f.write(response.content)
            else:
                dl = 0
                previous = 0
                total_length = int(total_length)
                for chunk in response.iter_content(chunk_size=4096):
                    dl += len(chunk)
                    f.write(chunk)
                    done = int(max_load_per * dl / total_length)
                    if done > previous:
                        previous = done
        return True
    except Exception as e:
        print(f"Error during download: {e}")
        return False

def background_task(filename: str, local_file: Union[str, Path], task_id: str, task_results: dict):
    result = load_data(filename, local_file)
    task_results[task_id] = result

task_results = {}

@f_app.post("/download/")
async def download_file(request: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = str(len(task_results) + 1)
    task_results[task_id] = None
    background_tasks.add_task(background_task, request.filename, request.local_file, task_id, task_results)
    return {"task_id": task_id}

@f_app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    result = task_results.get(task_id)
    if result is None:
        return {"task_id": task_id, "status": "In Progress"}
    return {"task_id": task_id, "status": "Completed", "result": result}

if __name__ == "__main__":
    """poetry run python main_fastapi.py"""
    uvicorn.run(f_app, host="127.0.0.1", port=8000)