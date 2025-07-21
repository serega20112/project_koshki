# Проект Koshki

## 📦 Установка и подготовка

### 🔹 1️⃣ Установка Docker

Если у тебя ещё нет Docker:

- [Скачать Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

### 🔹 2️⃣ Запуск контейнеров

в папке с docker-compose сделай:

```bash
docker-compose up --build
```
- Если всё хорошо, то:
  - Kibana доступна на ```localhost:5601```
  - Elastic доступен на ```localhost:9200```
  - RabbitMQ доступен на ```localhost:15672```


### 🔹 3️⃣  Установка Python-зависимостей

Убедись, что у тебя установлен Python 3.10+

Установи зависимости:
!!!Но сначала перейди в нужную директорию:
```bash
cd ..
```

```bash
pip install -r requirements.txt
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

