from fastapi import Request
from starlette.responses import Response
from datetime import datetime, timedelta
from src.infrastructure.rabbit_and_celery.scheduler.scheduler import scheduler

def publish_cat_event(event_data: dict):
    try:
        from src.infrastructure.rabbit_and_celery.message_broker.rabbitmq_pusher import RabbitMQPublisher
        publisher = RabbitMQPublisher()
        publisher.publish(event_data, routing_key="cat.created")
        print(f"✅ [SCHEDULED] Событие отправлено: {event_data}")
    except Exception as e:
        print(f"❌ [SCHEDULED] Ошибка при отправке события: {e}")

async def event_handler_middleware(request: Request, call_next):
    response: Response = await call_next(request)

    if hasattr(request.state, "cat_service"):
        service = request.state.cat_service
        if hasattr(service, "event") and service.event is not None:
            event = service.event

            try:
                seconds = 5
                run_date = datetime.now(scheduler.timezone) + timedelta(seconds=seconds)

                # Генерируем уникальный ID задачи, чтобы избежать дублей
                job_id = f"cat_event_{hash(str(event)) % 1000000}_{int(datetime.now().timestamp())}"

                scheduler.add_job(
                    func=publish_cat_event,
                    trigger='date',
                    run_date=run_date,
                    args=[event],
                    id=job_id,
                    replace_existing=True,
                )

                print(f"🕒 [MIDDLEWARE] Запланирована отправка события через {seconds} сек: {event}")
                service.event = None

            except Exception as e:
                print(f"❌ [MIDDLEWARE] Ошибка при планировании события: {e}")

    return response