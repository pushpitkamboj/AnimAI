from e2b import AsyncSandbox
from agent.graph_state import State
from e2b.sandbox.commands.command_handle import CommandExitException 
from e2b.exceptions import TimeoutException

from dotenv import load_dotenv
load_dotenv()
import os

account_id = os.getenv("ACCOUNT_ID")
secret_access_key = os.getenv("SECRET_ACCESS_KEY")
access_key_id = os.getenv("ACCESS_KEY_ID")

# Reuse sandbox instance across calls (keep-alive)
_sandbox_instance = None

async def get_or_create_sandbox(force_new=False):
    global _sandbox_instance
    if _sandbox_instance is None or force_new:
        if force_new and _sandbox_instance:
            try:
                await _sandbox_instance.close()
            except:
                pass  # Ignore errors when closing dead sandbox
        
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
    global _sandbox_instance
    scene_name = state["scene_name"]
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            sandbox = await get_or_create_sandbox(force_new=(attempt > 0))
            
            await sandbox.files.write(f'/home/user/{scene_name}.py', state["code"])
            
            try:
                # Render to LOCAL disk first (fast), then copy to bucket
                result = await sandbox.commands.run(
                    f'manim -ql /home/user/{scene_name}.py && '
                    f'cp -r /home/user/media/videos/{scene_name} /home/user/bucket/media/videos/',
                    timeout=500
                )
            except CommandExitException as error:
                return {"sandbox_error": str(error)}
            
            quality = "480p15"
            public_url = f"https://pub-b215a097b7b243dc86da838a88d50339.r2.dev/media/videos/{scene_name}/{quality}/{scene_name}.mp4"

            return {
                "sandbox_error": "No error",
                "video_url": public_url
            }
            
        except TimeoutException as e:
            # Sandbox timed out - reset and retry
            _sandbox_instance = None
            if attempt == max_retries - 1:
                return {"sandbox_error": f"Sandbox timeout after {max_retries} attempts: {str(e)}"}
            # Continue to next retry
        except Exception as e:
            return {"sandbox_error": f"Unexpected error: {str(e)}"}