# RabbitMQ: Краткая база знаний

## Что такое RabbitMQ
Message broker (брокер сообщений) - промежуточное ПО для обмена сообщениями между приложениями. Использует протокол AMQP.

## Основные концепции

### Producer (Производитель)
Отправляет сообщения в очередь.
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
connection.close()
```

### Consumer (Потребитель)
Получает и обрабатывает сообщения из очереди.
```python
def callback(ch, method, properties, body):
    print(f"Received {body}")

channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
channel.start_consuming()
```

### Queue (Очередь)
Буфер для хранения сообщений.
```python
channel.queue_declare(queue='hello', durable=True)  # durable - очередь переживет перезапуск
```

### Exchange (Обменник)
Маршрутизирует сообщения в очереди по правилам.

**Direct Exchange** - точное совпадение routing key:
```python
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
channel.basic_publish(exchange='direct_logs', routing_key='error', body=message)
```

**Fanout Exchange** - отправляет во все привязанные очереди:
```python
channel.exchange_declare(exchange='logs', exchange_type='fanout')
channel.basic_publish(exchange='logs', routing_key='', body=message)
```

**Topic Exchange** - паттерны в routing key (* - одно слово, # - ноль или более):
```python
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
channel.basic_publish(exchange='topic_logs', routing_key='kern.critical', body=message)
```

### Binding (Привязка)
Связь между exchange и queue.
```python
channel.queue_bind(exchange='logs', queue=queue_name)
```

## Важные параметры

### Acknowledgment (Подтверждение)
Гарантирует, что сообщение обработано.
```python
def callback(ch, method, properties, body):
    # обработка
    ch.basic_ack(delivery_tag=method.delivery_tag)  # ручное подтверждение

channel.basic_consume(queue='task_queue', on_message_callback=callback, auto_ack=False)
```

### Prefetch
Ограничивает количество необработанных сообщений у воркера.
```python
channel.basic_qos(prefetch_count=1)  # по одному сообщению за раз
```

### TTL (Time To Live)
Время жизни сообщения.
```python
channel.queue_declare(queue='hello', arguments={'x-message-ttl': 60000})  # 60 секунд
```

### Priority (Приоритет)
Сообщения с высоким приоритетом обрабатываются первыми.
```python
channel.queue_declare(queue='priority_queue', arguments={'x-max-priority': 10})
channel.basic_publish(
    exchange='',
    routing_key='priority_queue',
    body='Important',
    properties=pika.BasicProperties(priority=9)
)
```

## Паттерны использования

### Work Queue (Распределение задач)
```python
# Producer
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message,
    properties=pika.BasicProperties(delivery_mode=2)  # persistent message
)

# Consumer
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
```

### Publish/Subscribe
```python
# Publisher
channel.exchange_declare(exchange='logs', exchange_type='fanout')
channel.basic_publish(exchange='logs', routing_key='', body=message)

# Subscriber
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='logs', queue=queue_name)
```

### RPC (Remote Procedure Call)
```python
# Client
correlation_id = str(uuid.uuid4())
channel.basic_publish(
    exchange='',
    routing_key='rpc_queue',
    properties=pika.BasicProperties(reply_to=callback_queue, correlation_id=correlation_id),
    body=request
)
```

## Полезные команды CLI
```bash
rabbitmqctl list_queues                    # список очередей
rabbitmqctl list_exchanges                 # список обменников
rabbitmqctl purge_queue queue_name         # очистить очередь
rabbitmq-plugins enable rabbitmq_management # включить веб-интерфейс
```