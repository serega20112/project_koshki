from pydantic_settings import BaseSettings


class RabbitMQSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    exchange_name: str = "cats_event"
    queue_name: str = "cat_queue"
    routing_key: str = "cat.created"

    class Config:
        env_prefix = "RABBITMQ_"


rabbitmq_settings = RabbitMQSettings()
