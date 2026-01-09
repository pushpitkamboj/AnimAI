import os
from daytona import Daytona, Resources, CreateSandboxFromSnapshotParams, Image, CreateSnapshotParams, DaytonaConfig
from dotenv import load_dotenv
load_dotenv

DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY")

custom_image = Image.from_dockerfile("Dockerfile")

daytona = Daytona(DaytonaConfig(api_key=DAYTONA_API_KEY))

resources = Resources(
    cpu=4,  # 2 CPU cores
    memory=4,  # 4GB RAM
    disk=8,  # 8GB disk space
)

# Create the Snapshot and stream the build logs
daytona.snapshot.create(
    CreateSnapshotParams(
        name="manim_spanshot",
        image=custom_image,
        resources=resources
    ),
    on_logs=print,
)

