from e2b import AsyncSandbox
from agent.graph_state import State
from e2b.sandbox.commands.command_handle import CommandExitException 

from dotenv import load_dotenv
load_dotenv()
import os

account_id = os.getenv("ACCOUNT_ID")
secret_access_key = os.getenv("SECRET_ACCESS_KEY")
access_key_id = os.getenv("ACCESS_KEY_ID")

# Reuse sandbox instance across calls (keep-alive)
_sandbox_instance = None

async def get_or_create_sandbox():
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = await AsyncSandbox.create(
            template='2t56femtmrz3jfpfplcl',
            timeout=300  # Keep alive for 5 minutes
        )
        # One-time setup
        await _sandbox_instance.files.write('/root/.passwd-s3fs', f'{access_key_id}:{secret_access_key}')
        await _sandbox_instance.commands.run('sudo chmod 600 /root/.passwd-s3fs')
        await _sandbox_instance.files.make_dir('/home/user/bucket')
        await _sandbox_instance.commands.run(
            f'sudo s3fs -o url=https://{account_id}.r2.cloudflarestorage.com -o allow_other manim-videos /home/user/bucket'
        )
    return _sandbox_instance


async def execute_code_e2b(state: State):
    sandbox = await get_or_create_sandbox()
    
    scene_name = state["scene_name"]
    quality = "480p15"  # 480p15 for -ql, 1080p60 for -qh
    
    # Write the scene file
    await sandbox.files.write(f'/home/user/{scene_name}.py', state["code"])
    
    try:
        # Render to LOCAL disk (fast), then copy ONLY the final .mp4 to bucket
        result = await sandbox.commands.run(
            f'manim -ql /home/user/{scene_name}.py && '
            f'mkdir -p /home/user/bucket/v2_videos && '
            f'cp /home/user/media/videos/{scene_name}/{quality}/{scene_name}.mp4 '
            f'/home/user/bucket/v2_videos/',
            timeout=500
        )
    except CommandExitException as error:
        return {"sandbox_error": error}
    
    public_url = f"https://pub-b215a097b7b243dc86da838a88d50339.r2.dev/v2_videos/{scene_name}.mp4"

    return {
        "sandbox_error": "No error",
        "video_url": public_url
    }