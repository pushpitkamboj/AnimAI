from fastapi import FastAPI, HTTPException
import subprocess
import uuid
import os
import boto3
import datetime

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/render")
def render(payload: dict):
    # ---- Validate input ----
    code = payload.get("code")
    scene_name = payload.get("scene_name")

    if not code or not scene_name:
        raise HTTPException(400, "code and scene_name are required")

    request_id = payload.get("request_id", str(uuid.uuid4()))
    today = datetime.date.today().isoformat()

    # ---- Prepare paths ----
    src_file = f"/tmp/{request_id}.py"
    media_dir = "/tmp/media"
    os.makedirs(media_dir, exist_ok=True)

    # ---- Write Manim code ----
    with open(src_file, "w") as f:
        f.write(code)

    # ---- Execute Manim ----
    try:
        subprocess.run(
            [
                "manim",
                "-ql",
                src_file,
                scene_name,
                "--media_dir",
                media_dir
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"Manim failed: {e}")

    # ---- Verify output ----
    video_path = f"{media_dir}/videos/{request_id}/480p15/{scene_name}.mp4"
    if not os.path.exists(video_path):
        raise HTTPException(500, "Video not generated")

    skip_upload = os.environ.get("SKIP_UPLOAD", "0") == "1"

    if skip_upload:
        return {
            "video_url": f"file://{video_path}",
            "scene_name": scene_name,
            "request_id": request_id,
            "upload_skipped": True,
        }

    # ---- Upload to Cloudflare R2 ----
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )

    key = f"manim/{today}/{scene_name}/{request_id}.mp4"

    try:
        s3.upload_file(
            video_path,
            os.environ["R2_BUCKET"],
            key,
            ExtraArgs={"ContentType": "video/mp4"},
        )
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {e}")

    # ---- Return public URL ----
    public_url = f"https://pub-{os.environ['R2_ACCOUNT_ID']}.r2.dev/{key}"

    return {
        "video_url": public_url,
        "scene_name": scene_name,
        "request_id": request_id,
    }
