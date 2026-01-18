import asyncio
from e2b import AsyncTemplate, default_build_logger
from .template import template
from dotenv import load_dotenv
load_dotenv()


async def main():
    value = await AsyncTemplate.build(
        template,
        alias="vtxlabs",
        on_build_logs=default_build_logger(),
        cpu_count=4,  # CPU cores
    memory_mb=4096,  # Memory in MB
    )
    print(value)


if __name__ == "__main__":
    asyncio.run(main())