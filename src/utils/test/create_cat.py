import asyncio
import aiohttp
from time import time
from multiprocessing import Process, cpu_count
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

BASE_URL = "http://localhost:8000"
CONCURRENT_PROCESSES = cpu_count() -2
REQUESTS_PER_BATCH = 5000 # на 1 цикл, меняй для более большого количества запросов
SLEEP_BETWEEN_BATCHES = 0  # сек, для нон-стопа ставим 0

new_cat_data = {
    "id": 0,
    "name": "Fluffy",
    "age": 2,
    "color": "White",
    "breed": "Persian",
    "breed_id": 0,
}

update_cat_data = {
    "id": 1,
    "name": "FluffyUpdated",
    "age": 3,
    "color": "Gray",
    "breed": "Siamese",
    "breed_id": 1,
}


async def fire(session):
    tasks = []
    for _ in range(REQUESTS_PER_BATCH):
        tasks.append(session.post(f"{BASE_URL}/cats", json=new_cat_data))
        tasks.append(session.put(f"{BASE_URL}/cats/1", json=update_cat_data))
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    ok = sum(
        1
        for r in responses
        if isinstance(r, aiohttp.ClientResponse) and r.status == 200
    )
    print(f"Batch: {ok}/{len(tasks)} OK")


async def worker_loop():
    connector = aiohttp.TCPConnector(limit=5, force_close=False)
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        while True:
            await fire(session)
            if SLEEP_BETWEEN_BATCHES:
                await asyncio.sleep(SLEEP_BETWEEN_BATCHES)


def run_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker_loop())


if __name__ == "__main__":
    print(f"Launching {CONCURRENT_PROCESSES} workers. Hit Ctrl+C to stop.")
    start = time()

    procs = [Process(target=run_worker) for _ in range(CONCURRENT_PROCESSES)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"Completed in {time() - start:.2f}s")
