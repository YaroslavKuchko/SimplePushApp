import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp

import requests
import json
import uuid
import os
from plyer import notification
from plyer import vibrator


SERVER_URL = "http://138.124.113.77:8000"
DEVICE_CONFIG_FILE = "device_config.json"

class ModernButton(Button):
    """Современная кнопка с закругленными углами"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_bg, pos=self.update_bg)
        
    def update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.3, 0.3, 0.3, 1)  # Темно-серый цвет
            RoundedRectangle(pos=self.pos, size=self.size, radius=[15])

class StatusCard(BoxLayout):
    """Карточка статуса устройства"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = [dp(25), dp(20)]
        self.spacing = dp(5)
        
        with self.canvas.before:
            Color(0.25, 0.25, 0.25, 1)  # Темно-серый фон
            RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        
        self.bind(size=self.update_bg, pos=self.update_bg)
        
    def update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.25, 0.25, 0.25, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[20])

class SimplePushApp(App):
    def build(self):
        self.device_token = self.load_or_create_device_token()
        self.registered = False
        
        # Основной контейнер с прокруткой
        main_container = BoxLayout(orientation='vertical')
        
        # Заголовочная область
        header = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(20), dp(20), dp(20), dp(10)]
        )
        
        with header.canvas.before:
            Color(0.15, 0.15, 0.15, 1)  # Темный фон
            Rectangle(pos=header.pos, size=header.size)
        
        # Заголовок приложения
        title = Label(
            text='Simple Push',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(32),
            bold=True,
            color=(1, 1, 1, 1)  # Белый текст
        )
        header.add_widget(title)
        
        header.bind(size=lambda *args: self.update_header_bg(header), pos=lambda *args: self.update_header_bg(header))
        
        # Основной контент с прокруткой
        scroll = ScrollView()
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=[dp(25), dp(15), dp(25), dp(25)],
            spacing=dp(20)
        )
        content.bind(minimum_height=content.setter('height'))
        
        # Карточка статуса устройства
        status_card = StatusCard()
        
        # Статус устройства (только статус, без заголовков)
        self.status_label = Label(
            text='Инициализация...',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            color=(0.9, 0.9, 0.9, 1)  # Светлый текст для темной темы
        )
        status_card.add_widget(self.status_label)
        
        content.add_widget(status_card)
        
        # Кнопки действий
        # Кнопка получения ссылки
        self.get_link_btn = ModernButton(
            text='Получить ссылку',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(18),
            color=(1, 1, 1, 1)
        )
        self.get_link_btn.bind(on_press=self.get_link)
        content.add_widget(self.get_link_btn)
        
        scroll.add_widget(content)
        
        # Сборка интерфейса
        main_container.add_widget(header)
        main_container.add_widget(scroll)
        
        # Инициализация статуса
        self.status_label.text = "Готов к работе"
        self.get_link_btn.disabled = False
        
        return main_container
    
    def update_header_bg(self, header_widget):
        """Обновление фона заголовка"""
        header_widget.canvas.before.clear()
        with header_widget.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=header_widget.pos, size=header_widget.size)
    
    def load_or_create_device_token(self):
        """Загружает существующий device_token или создает новый"""
        try:
            if os.path.exists(DEVICE_CONFIG_FILE):
                with open(DEVICE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    device_token = config.get('device_token')
                    if device_token:
                        Logger.info(f"Loaded existing device token: {device_token[:8]}...")
                        return device_token
            
            # Создаем новый токен
            new_token = str(uuid.uuid4())
            self.save_device_token(new_token)
            Logger.info(f"Created new device token: {new_token[:8]}...")
            return new_token
            
        except Exception as e:
            Logger.error(f"Error loading device token: {e}")
            # Fallback на новый токен
            new_token = str(uuid.uuid4())
            self.save_device_token(new_token)
            return new_token
    
    def save_device_token(self, device_token):
        """Сохраняет device_token в файл"""
        try:
            config = {
                'device_token': device_token,
                'created_at': str(uuid.uuid4().time_low)  # Простая временная метка
            }
            with open(DEVICE_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            Logger.info(f"Device token saved to {DEVICE_CONFIG_FILE}")
        except Exception as e:
            Logger.error(f"Error saving device token: {e}")
    
    def auto_register_device(self):
        """Автоматическая регистрация устройства при запуске"""
        # Проверяем, есть ли уже сохраненная информация о регистрации
        if self.is_device_registered():
            self.status_label.text = f"✅ Уже зарегистрировано"
            self.status_label.color = (0.2, 0.8, 0.2, 1)  # Зеленый цвет
            self.registered = True
            Logger.info("Device already registered (from cache)")
            return
        
        self.status_label.text = "⏳ Регистрация..."
        
        try:
            response = requests.post(
                f"{SERVER_URL}/register_device",
                json={"device_token": self.device_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.registered = True
                self.status_label.text = f"✅ Зарегистрировано"
                self.status_label.color = (0.2, 0.8, 0.2, 1)  # Зеленый цвет
                self.save_registration_status(True)
                Logger.info(f"Device registered successfully: {data.get('device_id', 'N/A')}")
                
            else:
                self.status_label.text = f"❌ Ошибка регистрации: {response.status_code}"
                self.status_label.color = (0.8, 0.2, 0.2, 1)  # Красный цвет
                Logger.error(f"Registration failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.status_label.text = f"❌ Ошибка соединения"
            self.status_label.color = (0.8, 0.2, 0.2, 1)  # Красный цвет
            Logger.error(f"Registration connection error: {str(e)}")
    
    def is_device_registered(self):
        """Проверяет, зарегистрировано ли устройство (из кеша)"""
        try:
            if os.path.exists(DEVICE_CONFIG_FILE):
                with open(DEVICE_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('registered', False)
            return False
        except Exception as e:
            Logger.error(f"Error checking registration status: {e}")
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
            
            Logger.info(f"Registration status saved: {registered}")
        except Exception as e:
            Logger.error(f"Error saving registration status: {e}")
    
    def get_link(self, instance):
        """Получение ссылки с сервера и открытие в браузере"""
        self.get_link_btn.disabled = True
        self.get_link_btn.text = "Загрузка..."
        
        try:
            response = requests.get(f"{SERVER_URL}/get_link", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                link = data.get('link', 'https://google.com')
                
                
                # Открытие ссылки в браузере
                self.open_url(link)
                
                self.show_popup("Успех", f"Ссылка открыта:\n{link}")
                
            else:
                self.show_popup("Ошибка", f"Ошибка получения ссылки: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.show_popup("Ошибка", f"Ошибка соединения: {str(e)}")
            
        finally:
            self.get_link_btn.disabled = False
            self.get_link_btn.text = "Получить ссылку"
    
    
    def open_url(self, url):
        """Открытие URL в браузере"""
        try:
            # Для всех платформ используем webbrowser
            import webbrowser
            webbrowser.open(url)
                
        except Exception as e:
            Logger.error(f"Error opening URL: {e}")
            self.show_popup("Ошибка", f"Не удалось открыть ссылку: {str(e)}")
    
    def show_popup(self, title, message):
        """Показать современное всплывающее окно"""
        content = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(20))
        
        # Заголовок popup
        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(40),
            font_size=dp(22),
            bold=True,
            color=(1, 1, 1, 1)
        )
        content.add_widget(title_label)
        
        # Сообщение
        message_label = Label(
            text=message,
            size_hint_y=None,
            height=dp(60),
            font_size=dp(16),
            color=(0.8, 0.8, 0.8, 1),
            text_size=(dp(300), None),
            halign='center',
            valign='middle'
        )
        content.add_widget(message_label)
        
        # Кнопка закрытия
        close_btn = ModernButton(
            text='Закрыть',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.8, 0.5),
            auto_dismiss=True,
            background_color=(0.2, 0.2, 0.2, 1)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()
    
    def show_notification(self, title, message):
        """Показать локальное уведомление"""
        try:
            # Проверяем платформу и показываем уведомление только если возможно
            if platform == 'android' or platform == 'ios':
                notification.notify(
                    title=title,
                    message=message,
                    app_name='Simple Push App',
                    timeout=10
                )
                
                # Вибрация при получении уведомления
                try:
                    if hasattr(vibrator, 'vibrate'):
                        vibrator.vibrate(1.0)
                except:
                    pass
            else:
                # Для десктопа показываем popup вместо уведомления
                Clock.schedule_once(lambda dt: self.show_popup(title, message), 0.1)
                
        except Exception as e:
            Logger.error(f"Notification error: {e}")
            # Fallback на popup
            Clock.schedule_once(lambda dt: self.show_popup(title, message), 0.1)
    
    def on_start(self):
        """Вызывается при запуске приложения"""
        super().on_start()
        
        # Автоматически регистрируем устройство при запуске
        Clock.schedule_once(lambda dt: self.auto_register_device(), 0.5)
        
        # Автоматически получаем ссылку при запуске
        Clock.schedule_once(lambda dt: self.get_link(None), 2)
        
        # Показываем приветственное уведомление
        Clock.schedule_once(
            lambda dt: self.show_notification(
                "Добро пожаловать!",
                "Приложение запущено"
            ), 3
        )

if __name__ == '__main__':
    SimplePushApp().run()
