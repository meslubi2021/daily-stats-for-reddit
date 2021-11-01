import asyncio

CONCURRENCY = 10

async def gather_with_concurrency(*tasks):
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async def sem_task(task):
        async with semaphore:
            return await asyncio.ensure_future(task)
    return await asyncio.gather(*(sem_task(task) for task in tasks))
