# stress_tester.py

import asyncio
import aiohttp
import random
import string
import sys
from time import time
from multiprocessing import Process, cpu_count
from typing import Dict, Any, List

# Для Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Настройки
BASE_URL = "http://localhost:8000"
CONCURRENT_PROCESSES = cpu_count() - 2
REQUESTS_PER_BATCH = 1000  # запросов на батч
SLEEP_BETWEEN_BATCHES = 0  # 0 = нон-стоп

# Список имён котов (для рандома)
CAT_NAMES = [
    "Whiskers", "Fluffy", "Mittens", "Shadow", "Luna", "Bella", "Oliver", "Simba",
    "Tiger", "Chloe", "Leo", "Nala", "Milo", "Daisy", "Coco", "Max", "Lucy", "Oscar"
]

# Цвета и породы
COLORS = ["White", "Black", "Gray", "Orange", "Calico", "Tabby", "Brown", "Cream"]
BREEDS = ["Persian", "Siamese", "Maine Coon", "Bengal", "Sphynx", "British Shorthair", "Abyssinian", "Exotic"]

# Валидные данные
VALID_CAT = {
    "name": "Fluffy",
    "age": 2,
    "color": "White",
    "breed": "Persian",
    "breed_id": 1,
}

# Битые данные — для теста DLQ, валидации и т.п.
INVALID_CATS = [
    {"name": "", "age": 2, "color": "Red", "breed": "Bug", "breed_id": 999},  # пустое имя
    {"name": "Null", "age": -5, "color": "Void", "breed": "Error", "breed_id": 0},  # отрицательный возраст
    {"name": "🔥", "age": "abc", "color": "Rainbow", "breed": "Chaos", "breed_id": "NaN"},  # типы не те
    {"extra_field": "hack", "name": "HackerCat"},  # лишние поля
    {},  # пустота
]


async def random_string(length=5):
    return ''.join(random.choices(string.ascii_letters, k=length))


async def random_cat_data(valid=True) -> Dict[str, Any]:
    if not valid:
        return random.choice(INVALID_CATS)

    return {
        "name": random.choice(CAT_NAMES),
        "age": random.randint(1, 20),
        "color": random.choice(COLORS),
        "breed": random.choice(BREEDS),
        "breed_id": random.randint(1, 10),
    }


async def fire(session: aiohttp.ClientSession, stats: Dict[str, int]):
    tasks: List[asyncio.Task] = []
    endpoints = [
        ("POST", "/cats"),
        ("PUT", "/cats/{id}"),
        ("GET", "/cats/{id}"),
        ("DELETE", "/cats/{id}"),
    ]

    for _ in range(REQUESTS_PER_BATCH):
        method, path = random.choice(endpoints)
        cat_id = random.randint(1, 50)  # предполагаем, что коты есть

        # Подставляем ID
        url = f"{BASE_URL}{path.format(id=cat_id)}"

        # Решаем: валидный или битый запрос
        is_valid = random.random() > 0.3  # 70% валидных, 30% битых

        if method == "POST":
            data = await random_cat_data(valid=is_valid)
            task = session.post(url, json=data, timeout=5)
        elif method == "PUT":
            data = await random_cat_data(valid=is_valid)
            task = session.put(url, json=data, timeout=5)
        elif method == "GET":
            task = session.get(url, timeout=5)
        elif method == "DELETE":
            task = session.delete(url, timeout=5)
        else:
            continue

        tasks.append(task)

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in responses:
        if isinstance(resp, Exception):
            stats["errors"] += 1
            continue
        if isinstance(resp, aiohttp.ClientResponse):
            if resp.status in (200, 201, 204):
                stats["success"] += 1
            elif resp.status == 404:
                stats["not_found"] += 1
            elif resp.status == 422:
                stats["validation_errors"] += 1
            else:
                stats["failed"] += 1
            resp.release()


async def worker_loop(worker_id: int):
    connector = aiohttp.TCPConnector(limit=20, force_close=False, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=10)
    stats = {
        "success": 0, "failed": 0, "errors": 0, "not_found": 0, "validation_errors": 0
    }

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        batch = 0
        while True:
            batch += 1
            await fire(session, stats)

            if batch % 5 == 0:  # Каждые 5 батчей — статистика
                total = sum(stats.values())
                if total > 0:
                    print(
                        f"[Worker-{worker_id}] "
                        f"🚀 {stats['success']} OK | "
                        f"⚠️ {stats['validation_errors']} 422 | "
                        f"❌ {stats['failed']} Failed | "
                        f"👻 {stats['not_found']} 404 | "
                        f"💥 {stats['errors']} Err | "
                        f"Total: {total}"
                    )

            if SLEEP_BETWEEN_BATCHES:
                await asyncio.sleep(SLEEP_BETWEEN_BATCHES)


def run_worker(worker_id: int):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(worker_loop(worker_id))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    print(f"🔥 ЗАПУЩЕН СПАМЕР НА {CONCURRENT_PROCESSES} ПРОЦЕССОВ")
    print(f"🎯 Цель: {BASE_URL}")
    print(f"📦 {REQUESTS_PER_BATCH} запросов на батч, нон-стоп")
    print(f"🎲 Рандом: POST/PUT/GET/DELETE, валидные/битые данные")
    print("💀 Нажми Ctrl+C для остановки\n")

    start = time()
    try:
        procs = [
            Process(target=run_worker, args=(i,))
            for i in range(CONCURRENT_PROCESSES)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 Остановка всех воркеров...")
    finally:
        total_time = time() - start
        print(f"\n✅ Тест завершён за {total_time:.2f} сек")
        print(f"⚡ Средняя скорость: ~{int(CONCURRENT_PROCESSES * REQUESTS_PER_BATCH / total_time)} req/sec")