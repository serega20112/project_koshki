from fastapi import Request
from src.infrastructure.rabbit_and_celery.message_broker.rabbitmq_pusher import (
    RabbitMQPublisher,
)

publisher = RabbitMQPublisher()


async def event_handler_middleware(request: Request, call_next):
    response = await call_next(request)

    if hasattr(request.state, "cat_service"):
        service = request.state.cat_service
        if hasattr(service, "event") and service.event is not None:
            event = service.event

            try:
                # Публикуем через глобальный publisher
                publisher.publish(event, routing_key="cat.created")
                print(f"✅ [MIDDLEWARE] Событие отправлено: {event}")

                # Очищаем
                service.event = None

            except Exception as e:
                print(f"❌ [MIDDLEWARE] Ошибка публикации: {e}")

    return response
