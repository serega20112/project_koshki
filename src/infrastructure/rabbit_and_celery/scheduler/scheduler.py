from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

# Храним задачи в БД — чтобы не терялись при перезапуске
# jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.db")} пока что уберу

executors = {"default": ThreadPoolExecutor(5)}

scheduler = AsyncIOScheduler(
    executors=executors,
    timezone="UTC",
)


def start_scheduler():
    scheduler.start()
    print("Шедулер запущен")


def shutdown_scheduler():
    scheduler.shutdown()
    print("Шедулер остановлен")
