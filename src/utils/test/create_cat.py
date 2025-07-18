import requests
import random
import string

# Настройки
API_URL = "http://localhost:8000/cats"  # URL вашего FastAPI маршрута
NUM_CATS = 100  # Количество кошек для создания

# Списки для генерации случайных данных
names = [
    "Luna",
    "Milo",
    "Bella",
    "Simba",
    "Leo",
    "Lola",
    "Max",
    "Nala",
    "Oliver",
    "Chloe",
]
colors = ["Black", "White", "Gray", "Orange", "Brown", "Spotted"]
breeds = ["Persian", "Siamese", "Maine Coon", "Ragdoll", "British Shorthair"]


# Функция для генерации данных кошки
def generate_cat_data():
    return {
        "id": "".join(random.choices(string.digits, k=5)),  # Уникальный 5-значный ID
        "name": random.choice(names),
        "age": random.randint(1, 15),  # Возраст от 1 до 15 лет
        "color": random.choice(colors),
        "breed": random.choice(breeds),
        "breed_id": random.randint(
            100, 999
        ),  # Поле с подчеркиванием для соответствия CatDTO
    }


# Основной цикл
cats_created = 0

print(f"Начало создания {NUM_CATS} кошек...")

for _ in range(NUM_CATS):
    cat_data = generate_cat_data()
    try:
        response = requests.post(
            API_URL, json=cat_data, headers={"Content-Type": "application/json"}
        )
        if response.status_code in [200, 201]:
            print(f"Успешно создана кошка: {cat_data['name']} (ID: {cat_data['id']})")
            cats_created += 1
        else:
            print(
                f"Ошибка при создании кошки {cat_data['name']}: {response.status_code} - {response.text}"
            )
    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения для кошки {cat_data['name']}: {e}")

print(f"\nЗавершено.")
print(f"Создано {cats_created} кошек из {NUM_CATS}.")

if cats_created < NUM_CATS:
    print(f"Создано меньше кошек из-за ошибок. Проверьте логи выше.")
