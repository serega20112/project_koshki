# 🐇 RabbitMQ — краткая база знаний

## Что такое очередь?

Очередь (queue) — структура данных, где первым пришёл — первым обработан (FIFO).  
В RabbitMQ — это буфер, куда отправляются сообщения, ожидающие обработки.

Пример:  
```python  
queue = ["msg1", "msg2"]  # первый войдёт — первым выйдет
```
---

## Что такое Producer?

Producer — это отправитель сообщений в очередь.

Пример:  
```python  
channel.basic_publish(exchange='', routing_key='hello', body='Привет!')
```
---

## Что такое Consumer?

Consumer — получатель сообщений из очереди.

Пример:  
```python  
channel.basic_consume(queue='hello', on_message_callback=callback)
```
---

## Что такое Exchange?

Exchange — маршрутизатор сообщений. Он принимает сообщение от продюсера и решает, в какую очередь отправить его.

Пример:  
```python  
channel.exchange_declare(exchange='logs', exchange_type='fanout')
```
---

## Что такое Routing Key?

Routing Key — строка, определяющая, в какую очередь отправить сообщение. Используется вместе с exchange.

Пример:  
```python  
channel.basic_publish(exchange='direct_logs', routing_key='info', body='Log!')
```
---

## Быстрый запуск RabbitMQ в Docker

```bash  
docker run -d --hostname rabbit --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
---

## Простой пример на Python (pika)

Отправка:  
```python  
import pika  
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))  
channel = connection.channel()  
channel.queue_declare(queue='hello')  
channel.basic_publish(exchange='', routing_key='hello', body='Привет!')  
connection.close()
```
Получение:  
```python  
import pika  
def callback(ch, method, properties, body):  
    print(f"Получено: {body.decode()}")  
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))  
channel = connection.channel()  
channel.queue_declare(queue='hello')  
channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)  
channel.start_consuming()
```
---

## Примечание

- Используй `pika` для синхронного кода, `aio-pika` — для асинхронного.
- RabbitMQ отлично подходит для микросервисов и фоновых задач.
- Всегда оборачивай соединения и каналы в try-finally или with-контекст для чистоты кода.
