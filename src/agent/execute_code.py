from e2b import Sandbox, AsyncSandbox
from agent.graph_state import State
from e2b.sandbox.commands.command_handle import CommandExitException 

from dotenv import load_dotenv
load_dotenv()
import os

account_id = os.getenv("account_id")
secret_access_key = os.getenv("secret_access_key")
access_key_id = os.getenv("access_key_id")

async def execute_code(state: State):
    sandbox = await AsyncSandbox.create(template='slo53v8nmn3kjq80sd59', timeout= 1000)
    await sandbox.files.make_dir('/home/user/bucket')
    
    await sandbox.files.write('/root/.passwd-s3fs', f'{access_key_id}:{secret_access_key}')
    await sandbox.commands.run('sudo chmod 600 /root/.passwd-s3fs')
    
    await sandbox.commands.run(f'sudo s3fs -o url=https://{account_id}.r2.cloudflarestorage.com -o allow_other manim-videos /home/user/bucket')

    await sandbox.files.write(f'/home/user/{state["scene_name"]}.py', state["code"]) #create a file scene.py inside the sandbox
    try:
        result = await sandbox.commands.run(f'manim --media_dir /home/user/bucket/media -r 640,360 --fps 15 /home/user/{state["scene_name"]}.py', timeout=900)
    except CommandExitException as error:
        return {
            "sandbox_error": error
        }
    await sandbox.kill()
    bucket_name = "manim-videos"
    scene_name = state["scene_name"]
    quality = "480p15" #default is 480p for development

    public_url = f"https://pub-b215a097b7b243dc86da838a88d50339.r2.dev/media/videos/{scene_name}/{quality}/{scene_name}.mp4"

    return {
        "sandbox_error": "No error",
        "video_url": public_url
    }
