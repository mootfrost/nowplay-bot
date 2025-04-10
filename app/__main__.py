import asyncio
from app import main


async def run():
    await main()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

