from pathlib import Path
import re
import os
import uuid
import time
from datetime import datetime
from daytona import Daytona, CreateSandboxFromSnapshotParams, VolumeMount
from agent.graph_state import State
import boto3
from botocore.config import Config

DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY")

# Cloudflare R2 credentials
R2_ACCOUNT_ID = os.getenv("ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
R2_BUCKET_NAME = "manim-videos"
R2_PUBLIC_URL = "https://pub-b215a097b7b243dc86da838a88d50339.r2.dev"


def _sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name).strip("_")


def _get_r2_client():
    """Create boto3 client for Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _upload_to_r2(local_content: bytes, r2_key: str) -> str:
    """Upload content to R2 and return public URL."""
    client = _get_r2_client()
    client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=r2_key,
        Body=local_content,
        ContentType="video/mp4",
    )
    return f"{R2_PUBLIC_URL}/{r2_key}"


def execute_manim_in_sandbox(state: State) -> dict:
    code = state["code"]
    scene_name = state["scene_name"]
    safe_name = _sanitize_name(scene_name) or "scene"
    
    # Initialize Daytona client
    daytona = Daytona()
    
    # Create or get a volume for manim media output
    volume = daytona.volume.get("manim-media", create=True)
    
    # Wait for volume to be ready (handle pending_create state)
    max_retries = 30
    for i in range(max_retries):
        volume = daytona.volume.get("manim-media")
        if volume.state == "ready":
            break
        elif volume.state in ("error", "deleted"):
            # Delete and recreate if in error state
            try:
                daytona.volume.delete(volume)
            except Exception:
                pass
            volume = daytona.volume.get("manim-media", create=True)
        print(f"Waiting for volume to be ready... (state: {volume.state})")
        time.sleep(2)
    else:
        return {
            "video_url": "",
            "sandbox_error": f"Volume failed to become ready after {max_retries * 2}s. State: {volume.state}"
        }
    
    # Mount path for the volume
    mount_path = "/home/daytona/media"
    
    # Create sandbox from snapshot with volume mounted
    sandbox = daytona.create(CreateSandboxFromSnapshotParams(
        snapshot="manim_spanshot",
        volumes=[VolumeMount(volumeId=volume.id, mountPath=mount_path)],
    ))
    
    try:
        # Create the scene file inside the sandbox
        src_file = f"/home/daytona/{safe_name}.py"
        sandbox.fs.upload_file(code.encode(), src_file)
        
        # Execute manim command - output to the mounted volume
        try:
            response = sandbox.process.exec(
                f"manim -ql {src_file} {safe_name} --media_dir {mount_path}"
            )
            print(f"Manim output: {response.result}")
            
            if response.exit_code != 0:
                return {
                    "video_url": "",
                    "sandbox_error": f"Manim execution failed: {response.result}"
                }
            
            # Video path in the volume
            quality = "480p15"  # default for -ql (low quality)
            video_path = f"{mount_path}/videos/{safe_name}/{quality}/{safe_name}.mp4"
            
            # Read the video file from sandbox
            video_content = sandbox.fs.download_file(video_path)
            
            # Upload to Cloudflare R2
            r2_key = f"media/videos/{safe_name}/{quality}/{safe_name}.mp4"
            public_url = _upload_to_r2(video_content, r2_key)
            
            print(f"Video uploaded to: {public_url}")
            
            return {
                "video_url": public_url,
                "sandbox_error": "No error"
            }
        except Exception as e:
            print(f"Execution failed: {e}")
            return {
                "video_url": "",
                "sandbox_error": f"Manim execution error: {str(e)}"
            }
    finally:
        sandbox.delete()