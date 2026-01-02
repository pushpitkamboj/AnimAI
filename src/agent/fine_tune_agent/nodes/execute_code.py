# from dotenv import load_dotenv
# load_dotenv()

# from e2b import Sandbox, AsyncSandbox
# from agent.fine_tune_agent.graph_state import State
# from e2b.sandbox.commands.command_handle import CommandExitException 
# import os
# import docker
# import os
# from docker.errors import ContainerError, ImageNotFound, APIError # <--- Add this!

# account_id = os.getenv("account_id")
# secret_access_key = os.getenv("secret_access_key")
# access_key_id = os.getenv("access_key_id")

# client = docker.from_env()


# import docker
# import os

# client = docker.from_env()

# #docs - https://docker-py.readthedocs.io/en/stable/images.html
# def ensure_image_exists(image_name="my-manim-interpreter:v1"):
#     try:
#         # Check if image already exists
#         client.images.get(image_name)
#         print(f"Image '{image_name}' found. Skipping build.")
#     except docker.errors.ImageNotFound:
#         print(f"Image '{image_name}' not found. Building now...")
#         # Path should be the directory containing your Dockerfile
#         image, logs = client.images.build(
#             path="/home/pushpit/Desktop/genAI/manimation/AnimAI", 
#             tag=image_name,
#             rm=True,  # Remove intermediate containers
#             nocache=False
#         )
#         for line in logs:
#             if 'stream' in line:
#                 print(line['stream'].strip())
#         print("Build complete.")

# # Call this once during your app's startup


# async def execute_code(state: State):
#     ensure_image_exists()
    
#     scene_name = state["CodeSceneName"]["scene_name"]
#     code_content = state["CodeSceneName"]["code"]
    
#     # 1. Create a temporary local file for the code
#     # This will be mounted into the container
#     local_tmp_path = f"/tmp/{scene_name}.py"
#     with open(local_tmp_path, "w") as f:
#         f.write(code_content)

#     # 2. Define the container command
#     # This mounts R2, runs Manim, and outputs to the bucket folder
#     container_command = (
#         f"bash -c 'echo {access_key_id}:{secret_access_key} > /root/.passwd-s3fs && "
#         f"chmod 600 /root/.passwd-s3fs && "
#         f"s3fs manim-videos /home/user/bucket -o url=https://{account_id}.r2.cloudflarestorage.com -o allow_other && "
#         f"manim --media_dir /home/user/bucket/media -ql /mnt/code/{scene_name}.py'"
#     )

#     try:
#         # 3. Run the container
#         # volumes: maps the host's /tmp file to the container's /mnt/code
#         container = client.containers.run(
#             image="my-manim-interpreter:v1", # Use your image here
#             command=container_command,
#             volumes={
#                 '/tmp': {'bind': '/mnt/code', 'mode': 'ro'},
#                 '/dev/fuse': {'bind': '/dev/fuse', 'mode': 'rw'} # Required for S3FS
#             },
#             privileged=True,     # MUST be true for S3FS/FUSE mounting
#             remove=True,         # Automatically delete container after exit
#             stderr=True,
#             stdout=True,
#             detach=False         # Wait for it to finish
#         )
        
#     except ContainerError as e:
#         # CASE 1: Python Error or Manim Command Failure
#         # e.stderr contains the traceback from the container
#         error_log = e.stderr.decode("utf-8")
#         return {
#             "sandbox_error": f"Python/Manim Error: {error_log}",
#             "video_url": None,
#             "exit_code": e.exit_status
#         }
        
#     except APIError as e:
#         # CASE 2: Docker Engine Error (e.g., out of memory, image not found)
#         return {
#             "sandbox_error": f"Docker Engine Error: {str(e)}",
#             "video_url": None
#         }
        
#     except Exception as e:
#         # CASE 3: General System Error (e.g., File I/O error on host)
#         return {
#             "sandbox_error": f"System Error: {str(e)}",
#             "video_url": None
#         }

#     # If we reached here, execution was successful
#     public_url = f"https://your-r2-public-url.dev/media/videos/{scene_name}/480p15/{scene_name}.mp4"

#     return {
#         "sandbox_error": "No error",
#         "video_url": public_url
#     }






from e2b import Sandbox, AsyncSandbox
from agent.graph_state import State
from e2b.sandbox.commands.command_handle import CommandExitException 
import asyncio

from dotenv import load_dotenv
load_dotenv()
import os

r2_account_id = os.getenv("R2_ACCOUNT_ID")
r2_secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
r2_access_key_id = os.getenv("R2_ACCESS_KEY_ID")

async def execute_code(state: State):
    sandbox = await AsyncSandbox.create(template='h7bsjoys6a5hlspy5gsx', timeout= 1000)
    await sandbox.files.make_dir('/home/user/bucket')
    
    await sandbox.files.write('/root/.passwd-s3fs', f'{r2_access_key_id}:{r2_secret_access_key}')
    await sandbox.commands.run('sudo chmod 600 /root/.passwd-s3fs')
    
    await sandbox.commands.run(f'sudo s3fs -o url=https://{r2_account_id}.r2.cloudflarestorage.com -o allow_other manim-videos /home/user/bucket')

    val = await sandbox.files.write(f'/home/user/{state["scene_name"]}.py', state["code"]) #create a file scene.py inside the sandbox
    print(val)
    print("========================================")
    try:
        result = await sandbox.commands.run(f'manim --media_dir /home/user/bucket/media -ql /home/user/{state["scene_name"]}.py', timeout=500) #change ql to qh for better resolution
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

