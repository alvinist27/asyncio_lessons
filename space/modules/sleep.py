from asyncio import sleep


async def async_sleep(tics=1):
    for _ in range(tics):
        await sleep(0)
