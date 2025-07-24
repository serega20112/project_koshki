from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Храним задачи в БД — чтобы не терялись при перезапуске
jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}

executors = {"default": ThreadPoolExecutor(5)}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    timezone="UTC",
)


def start_scheduler():
    scheduler.start()
    print("Шедулер запущен")


def shutdown_scheduler():
    scheduler.shutdown()
    print("Шедулер остановлен")
