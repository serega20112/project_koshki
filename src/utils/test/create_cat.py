import asyncio
import aiohttp
from time import time

# Базовый URL для локального хоста FastAPI
BASE_URL = "http://localhost:8000"

# Данные для регистрации новой кошки
new_cat_data = {
    "id": 0,
    "name": "Fluffy",
    "age": 2,
    "color": "White",
    "breed": "Persian",
    "breed_id": 0
}

# Данные для обновления кошки
update_cat_data = {
    "id": 1,
    "name": "FluffyUpdated",
    "age": 3,
    "color": "Gray",
    "breed": "Siamese",
    "breed_id": 1
}

async def register_cat(session, cat_data):
    async with session.post(f"{BASE_URL}/cats", json=cat_data) as response:
        if response.status == 200:
            print(f"Cat registered: {await response.text()}")
        else:
            print(f"Failed to register cat: {response.status}")

async def update_cat(session, cat_id, cat_data):
    async with session.put(f"{BASE_URL}/cats/{cat_id}", json=cat_data) as response:
        if response.status == 200:
            print(f"Cat updated: {await response.text()}")
        else:
            print(f"Failed to update cat: {response.status}")

async def run_test():
    async with aiohttp.ClientSession() as session:
        # Создаем список задач для имитации высокой нагрузки
        tasks = []
        requests_per_minute = 300000
        tasks_count = requests_per_minute // 60  # ~5000 запросов в секунду

        for _ in range(tasks_count):
            # Регистрация новой кошки
            tasks.append(register_cat(session, new_cat_data))
            # Обновление кошки
            tasks.append(update_cat(session, 1, update_cat_data))

        # Запускаем все задачи параллельно
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    start_time = time()
    asyncio.run(run_test())
    end_time = time()
    print(f"Test completed in {end_time - start_time:.2f} seconds")