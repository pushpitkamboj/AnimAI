import os
import uuid

import requests


def execute_code(state):
    request_id = str(uuid.uuid4())

    response = requests.post(
        os.environ["MANIM_WORKER_URL"] + "/render",
        json={
            "code": state["code"],
            "scene_name": state["scene_name"],
            "request_id": request_id,
        },
        timeout=900,
    )

    response.raise_for_status()
    data = response.json()

    return {
        "sandbox_error": "No error",
        "video_url": data["video_url"],
        "request_id": data["request_id"],
    }
