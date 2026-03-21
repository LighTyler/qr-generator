import aiohttp
import asyncio

from entrypoint.config import config


async def get_user(id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{config.service.url}/{id}") as response:
            data = await response.json()
            return data