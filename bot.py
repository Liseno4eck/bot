import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id
import time
import threading
import json
from datetime import datetime

# Конфигурация
TOKEN = "vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9Bme2Cx0UJDKud6S4bysNUO-w"
GROUP_ID = 240350664
OWNER_ID = 875762552

PEERS_FILE = "peers.json"
SETTINGS_FILE = "settings.json"
ACCESS_FILE = "access.json"

class PRBot:
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, GROUP_ID)
        
        self.peers = self.load_data(PEERS_FILE, [])
        self.settings = self.load_data(SETTINGS_FILE, {
            "broadcast_text": "",
            "is_running": False,
            "owner_id": OWNER_ID
        })
        self.access_list = self.load_data(ACCESS_FILE, [])
        
        if not isinstance(self.peers, list):
            self.peers = []
            self.save_data(PEERS_FILE, self.peers)
        if not isinstance(self.access_list, list):
            self.access_list = []
            self.save_data(ACCESS_FILE, self.access_list)
        
        # Запускаем поток для рассылки в фоновом режиме
        self.broadcast_thread = threading.Thread(target=self.broadcast_loop, daemon=True)
        self.broadcast_thread.start()
    
    def load_data(self, filename, default):
        """
        Функция для загрузки данных из JSON-файла.
        Если файл не найден или данные повреждены, загружает значение по умолчанию.
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Сохраняем значение по умолчанию и возвращаем его
            self.save_data(filename, default)
            return default
    
    def save_data(self, filename, data):
        """Функция для сохранения данных в JSON-файл."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Проверка, является ли пользователь владельцем
    def is_owner(self, user_id):
        return user_id == self.settings["owner_id"]
    
    # Проверяет, имеет ли пользователь доступ к боту
    def has_access(self, user_id):
        return self.is_owner(user_id) or user_id in self.access_list
    
    # Добавляет пользователя в список доступа
    def add_access(self, user_id):
        if user_id not in self.access_list:
            self.access_list.append(user_id)
            self.save_data(ACCESS_FILE, self.access_list)
            return True
        return False
    
    # Удаляет пользователя из списка доступа
    def remove_access(self, user_id):
        if user_id in self.access_list:
            self.access_list.remove(user_id)
            self.save_data(ACCESS_FILE, self.access_list)
            return True
        return False
    
    # Добавляет беседу в список для рассылки
    def add_peer(self, peer_id):
        if peer_id not in self.peers:
            self.peers.append(peer_id)
            self.save_data(PEERS_FILE, self.peers)
            return True
        return False
    
    # Удаляет беседу из списка для рассылки
    # В исходном коде была ошибка: функция вызывала метод append вместо remove
    def remove_peer(self, peer_id):
        if peer_id in self.peers:
            self.peers.remove(peer_id)  # Исправлено: теперь используется remove
            self.save_data(PEERS_FILE, self.peers)
            return True
        return False
    
    # Отправляет сообщение в указанную беседу
    def send_message(self, peer_id, text):
        try:
            self.vk.messages.send(
                peer_id=peer_id,
                message=text,
                random_id=get_random_id()
            )
        # Исправлено: `excep` заменено на `except`
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
    
    # Функция для отправки одного сообщения всем целевым беседам
    def broadcast_message(self):
        if not self.settings["broadcast_text"]:
            return
        for peer_id in self.peers:
            try:
                self.vk.messages.send(
                    peer_id=peer_id,
                    message=self.settings["broadcast_text"],
                    random_id=get_random_id()
                )
                time.sleep(1)  # Небольшая пауза между сообщениями, чтобы не попасть под ограничения VK
            except Exception as e:
                print(f"Ошибка: {e}")

    # Бесконечный цикл, который проверяет, нужно ли делать рассылку, и выполняет её
    def broadcast_loop(self):
        while True:
            if self.settings["is_running"] and self.settings["broadcast_text"] and self.peers:
                self.broadcast_message()
            time.sleep(3600)  # Проверяем раз в час
    
    # Обрабатывает команды, полученные от пользователей
    def handle_command(self, message):
        text = message.get('text', '').strip()
        user_id = message['from_id']
        peer_id = message['peer_id']
        
        if not text.startswith('/'):
            return  # Если сообщение не начинается с /, это не команда, игнорируем
        
        parts = text.split('\n', 1)
        command = parts[0].lower().strip()
        command_text = parts[1] if len(parts) > 1 else ""
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Команда: {command}, Текст: {command_text}")
        
        ### Команды для владельца
        if command == '/+доступ':
            if not self.is_owner(user_id):
                self.send_message(peer_id, "⛔ Только владелец может выдавать доступ.")
                return
            if not command_text.strip():
                self.send_message(peer_id, "⚠️ Укажите ID пользователя.")
                return
            try:
                target_id = int(command_text.strip())
                if self.add_access(target_id):
                    self.send_message(peer_id, f"✅ Доступ выдан пользователю {target_id}")
                else:
                    self.send_message(peer_id, f"ℹ️ У пользователя {target_id} уже есть доступ")
            except ValueError:
                self.send_message(peer_id, "⚠️ Неверный ID.")
            return

        elif command == '/-доступ':
            if not self.is_owner(user_id):
                self.send_message(peer_id, "⛔ Только владелец может забирать доступ.")
                return
            if not command_text.strip():
                self.
