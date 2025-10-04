"""
SimplePush Android App for Android Studio
Использует ChaquoPy для запуска Python на Android
"""

import os
import json
import uuid
import requests
import threading
import time
from datetime import datetime

# Конфигурация
SERVER_URL = "http://138.124.113.77:8000"
DEVICE_CONFIG_FILE = "device_config.json"

class SimplePushApp:
    def __init__(self):
        self.device_token = self.load_or_create_device_token()
        self.registered = False
        self.running = True
        
    def load_or_create_device_token(self):
        """Загружает существующий device_token или создает новый"""
        try:
            if os.path.exists(DEVICE_CONFIG_FILE):
                with open(DEVICE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    device_token = config.get('device_token')
                    if device_token:
                        print(f"Loaded existing device token: {device_token[:8]}...")
                        return device_token
            
            # Создаем новый токен
            new_token = str(uuid.uuid4())
            self.save_device_token(new_token)
            print(f"Created new device token: {new_token[:8]}...")
            return new_token
            
        except Exception as e:
            print(f"Error loading device token: {e}")
            # Fallback на новый токен
            new_token = str(uuid.uuid4())
            self.save_device_token(new_token)
            return new_token
    
    def save_device_token(self, device_token):
        """Сохраняет device_token в файл"""
        try:
            config = {
                'device_token': device_token,
                'created_at': datetime.now().isoformat()
            }
            with open(DEVICE_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Device token saved to {DEVICE_CONFIG_FILE}")
        except Exception as e:
            print(f"Error saving device token: {e}")
    
    def is_device_registered(self):
        """Проверяет, зарегистрировано ли устройство (из кеша)"""
        try:
            if os.path.exists(DEVICE_CONFIG_FILE):
                with open(DEVICE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('registered', False)
            return False
        except Exception as e:
            print(f"Error checking registration status: {e}")
            return False
    
    def save_registration_status(self, registered):
        """Сохраняет статус регистрации в конфигурацию"""
        try:
            config = {}
            if os.path.exists(DEVICE_CONFIG_FILE):
                with open(DEVICE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            
            config['registered'] = registered
            config['device_token'] = self.device_token
            
            with open(DEVICE_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"Registration status saved: {registered}")
        except Exception as e:
            print(f"Error saving registration status: {e}")
    
    def register_device(self):
        """Регистрация устройства на сервере"""
        if self.is_device_registered():
            print("✅ Device already registered")
            self.registered = True
            return True
        
        print("⏳ Registering device...")
        
        try:
            response = requests.post(
                f"{SERVER_URL}/register_device",
                json={"device_token": self.device_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.registered = True
                self.save_registration_status(True)
                print(f"✅ Device registered successfully: {data.get('device_id', 'N/A')}")
                return True
                
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Registration connection error: {str(e)}")
            return False
    
    def get_link(self):
        """Получение ссылки с сервера"""
        try:
            response = requests.get(f"{SERVER_URL}/get_link", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                link = data.get('link', 'https://google.com')
                print(f"✅ Link received: {link}")
                return link
                
            else:
                print(f"❌ Error getting link: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {str(e)}")
            return None
    
    def start_background_tasks(self):
        """Запуск фоновых задач"""
        def background_worker():
            while self.running:
                try:
                    # Проверяем регистрацию каждые 30 секунд
                    if not self.registered:
                        self.register_device()
                    
                    # Получаем ссылку каждые 60 секунд
                    link = self.get_link()
                    if link:
                        # Здесь можно добавить логику для открытия ссылки
                        # или отправки уведомления
                        pass
                    
                    time.sleep(30)  # Проверка каждые 30 секунд
                    
                except Exception as e:
                    print(f"Background task error: {e}")
                    time.sleep(60)  # При ошибке ждем дольше
        
        # Запускаем фоновый поток
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        print("Background tasks started")
    
    def stop(self):
        """Остановка приложения"""
        self.running = False
        print("Application stopped")
    
    def run(self):
        """Основной цикл приложения"""
        print("SimplePush App starting...")
        print(f"Device token: {self.device_token[:8]}...")
        
        # Регистрируем устройство
        self.register_device()
        
        # Запускаем фоновые задачи
        self.start_background_tasks()
        
        # Получаем первую ссылку
        link = self.get_link()
        if link:
            print(f"Initial link: {link}")
        
        print("SimplePush App is running...")
        print("Press Ctrl+C to stop")
        
        try:
            # Основной цикл
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()

# Точка входа для Android Studio
def main():
    """Главная функция для запуска в Android Studio"""
    app = SimplePushApp()
    app.run()

if __name__ == "__main__":
    main()