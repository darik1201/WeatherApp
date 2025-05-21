import os
import sys
import json
import sqlite3
import requests
import redis
from dotenv import load_dotenv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QLineEdit, QPushButton, QVBoxLayout,
    QWidget, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt
load_dotenv()
API_KEY = os.getenv("OWM_API_KEY")
class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Погодное приложение")
        self.setFixedSize(400, 450)
        try:
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                socket_connect_timeout=3
            )
            self.redis.ping()
        except redis.ConnectionError:
            print("Redis недоступен, работаем без кэша")
            self.redis = None
        self.conn = sqlite3.connect("weather.db")
        self.cursor = self.conn.cursor()
        self._init_db()
        self._create_ui()
    def _init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                temperature FLOAT,
                humidity INTEGER,
                wind_speed FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _create_ui(self):
        self.city_input = QLineEdit(placeholderText="Введите город")
        self.city_input.setStyleSheet("font-size: 14px; padding: 5px;")
        self.search_btn = QPushButton("Узнать погоду")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.search_btn.clicked.connect(self._fetch_weather)
        self.weather_icon = QLabel()
        self.weather_icon.setAlignment(Qt.AlignCenter)
        self.weather_icon.setFixedSize(100, 100)
        self.temp_label = QLabel("Температура: --°C")
        self.temp_label.setStyleSheet("font-size: 16px;")
        self.humidity_label = QLabel("Влажность: --%")
        self.humidity_label.setStyleSheet("font-size: 16px;")
        self.wind_label = QLabel("Ветер: -- м/с")
        self.wind_label.setStyleSheet("font-size: 16px;")
        self.history_label = QLabel("Последние запросы:\n--")
        self.history_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout = QVBoxLayout()
        layout.addWidget(self.city_input)
        layout.addWidget(self.search_btn)
        layout.addSpacing(10)
        layout.addWidget(self.weather_icon)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.humidity_label)
        layout.addWidget(self.wind_label)
        layout.addSpacing(15)
        layout.addWidget(QLabel("История:"))
        layout.addWidget(self.history_label)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
                font-family: Arial;
            }
        """)

    def _fetch_weather(self):
        city = self.city_input.text().strip()
        if not city:
            self._show_error("Введите название города")
            return
        try:
            cached_data = None
            if self.redis:
                cached_data = self.redis.get(f"weather:{city}")
                if cached_data:
                    data = json.loads(cached_data)
            if not cached_data:
                data = self._get_weather_from_api(city)
                if self.redis:
                    self.redis.setex(f"weather:{city}", 1800, json.dumps(data))
                self._save_to_db(city, data)
            self._update_ui(data)
            self._update_history()
        except requests.exceptions.RequestException:
            self._show_error("Ошибка подключения к интернету")
        except Exception as e:
            self._show_error(f"Ошибка: {str(e)}")
    def _get_weather_from_api(self, city):
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(error_data.get("message", "Неизвестная ошибка API"))
        weather_data = response.json()
        return {
            "temp": weather_data["main"]["temp"],
            "humidity": weather_data["main"]["humidity"],
            "wind": weather_data["wind"]["speed"],
            "icon": weather_data["weather"][0]["icon"]
        }
    def _save_to_db(self, city, data):
        self.cursor.execute(
            "INSERT INTO weather_history (city, temperature, humidity, wind_speed) VALUES (?, ?, ?, ?)",
            (city, data["temp"], data["humidity"], data["wind"])
        )
        self.conn.commit()
    def _update_ui(self, data):
        self.temp_label.setText(f"Температура: {data['temp']}°C")
        self.humidity_label.setText(f"Влажность: {data['humidity']}%")
        self.wind_label.setText(f"Ветер: {data['wind']} м/с")
        icon_url = f"http://openweathermap.org/img/wn/{data['icon']}@2x.png"
        icon_data = requests.get(icon_url).content
        pixmap = QPixmap()
        pixmap.loadFromData(icon_data)
        painter = QPainter(pixmap)
        pen = QPen(QColor(200, 200, 255))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(pixmap.rect().adjusted(1, 1, -1, -1))
        painter.end()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(3, 3)
        self.weather_icon.setGraphicsEffect(shadow)
        self.weather_icon.setPixmap(pixmap)
    def _update_history(self):
        self.cursor.execute(
            "SELECT city, temperature FROM weather_history ORDER BY timestamp DESC LIMIT 5"
        )
        history = self.cursor.fetchall()
        text = "Последние запросы:\n" + "\n".join(
            f"{city}: {temp}°C" for city, temp in history
        )
        self.history_label.setText(text)

    def _show_error(self, text):
        self.temp_label.setText(text)
        self.humidity_label.clear()
        self.wind_label.clear()
        self.weather_icon.clear()
        self.weather_icon.setGraphicsEffect(None)

app = QApplication(sys.argv)
window = WeatherApp()
window.show()
sys.exit(app.exec_())