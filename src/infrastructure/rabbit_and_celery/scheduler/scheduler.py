from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

executors = {"default": ThreadPoolExecutor(5)}

scheduler = AsyncIOScheduler(
    executors=executors,
    timezone="UTC",
)


def start_scheduler():
    scheduler.start()
    print("scheduler запущен")


def shutdown_scheduler():
    scheduler.shutdown()
    print("scheduler остановлен")
