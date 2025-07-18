# Проект Koshki

## 📦 Установка и подготовка

### 🔹 1️⃣ Установка Docker

Если у тебя ещё нет Docker:

- [Скачать Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

### 🔹 2️⃣ Запуск Elasticsearch

Запусти локально **Elasticsearch** версии 8.x (проект протестирован на 8.13.0):

```bash
docker run --name elastic-local -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.13.0
````

✅ Убедись, что Elasticsearch доступен по адресу:

```
http://localhost:9200
```

---

### 🔹 3️⃣ Запуск Kibana

Запусти **Kibana** через Docker:

```bash
docker run --name kibana-local -p 5601:5601 --link elastic-local:elasticsearch kibana:8.13.0
```

✅ Kibana откроется по адресу:

```
http://localhost:5601
```

---

### 🔹 4️⃣ Установка Python-зависимостей

Убедись, что у тебя установлен Python 3.10+

Установи зависимости:
```bash
pip install fastapi uvicorn elasticsearch==8.7.0 python-json-logger aio-pika==9.4.0
```

❗ Важно: Используй клиент **elasticsearch** версии 8.x для совместимости с сервером 8.x

---

## ⚙️ Middleware логирования FastAPI

* Логирует входящий запрос с полями:

  ```
  @timestamp, level, logger, class, event, message, summary, ErrClass, ErrMethod, params
  ```
---

## ⚙️ Настройка ElasticsearchHandler

* Отправляет логи в индекс **koshki-logs**
* Обрабатывает ошибки отправки и выводит сообщения в консоль для отладки

---

## ⚙️ Настройка Kibana

1️⃣ Перейди в Kibana → **Stack Management** → **Index Patterns (или Data Views)**
2️⃣ Создай новый индекс-паттерн:

```
koshki-logs*
```

3️⃣ Выбери поле **@timestamp** как поле для временной фильтрации
4️⃣ Сохрани индекс-паттерн

---

## ✅ Проверка работоспособности

Запусти FastAPI приложение:

```bash
uvicorn src.interface.main:app --reload
```

Сделай любой запрос к серверу (например, получи список всех кошек).

✅ После запроса:

* Проверь в Kibana → **Discover**
* Выбери индекс-паттерн `koshki-logs*`
* Убедись, что логи появляются с правильной временной меткой и полями

