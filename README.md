
# Погодное приложение на PyQt5

Приложение для просмотра текущей погоды в любом городе мира с использованием OpenWeatherMap API.

## Особенности

- Поиск текущей погоды по названию города
- Кэширование запросов в Redis (на 30 минут)
- Сохранение истории запросов в SQLite
- Удобный интерфейс с историей последних запросов
- Кроссплатформенная работа (Windows/Linux/macOS)

## Технологии

- **Python 3.8+**
- **PyQt5** - графический интерфейс
- **OpenWeatherMap API** - данные о погоде
- **Redis** - кэширование запросов
- **SQLite** - хранение истории

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-username/weather-app.git
cd weather-app
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и добавьте API-ключ:
```ini
OWM_API_KEY=ваш_ключ_от_openweathermap
```

4. Запустите Redis:
```bash
docker run -p 6379:6379 --name my-redis -d redis
```

5. Запустите приложение:
```bash
python weather_app.py
```

## Скриншоты
![image](https://github.com/user-attachments/assets/cc77a472-8f76-4558-80b0-a977d3823fe7)

