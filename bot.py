import re
import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id
import time
import threading
import json
from datetime import datetime

#Конфигурация
TOKEN = "vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9Bme2Cx0UJDKud6S4bysNUO-w"
GROUP_ID = 240350664
OWNER_ID = 875762552

PEERS_FILE = "peers.json"
SETTINGS_FILE = "settings.json"
ACCESS_FILE = "access.json"

class PRBot:
    def extract_user_id(self, message, text):
    # Пересланное сообщение
        fwd = message.get("fwd_messages", [])
        if fwd:
           return fwd[0].get("from_id")

    # Упоминание [id123|Имя]
    match = re.search(r"\[id(\d+)\|", text)
    if match:
        return int(match.group(1))

    text = text.strip().replace("@", "")
    text = text.replace("https://vk.com/", "").replace("http://vk.com/", "")

    # Числовой ID
    if text.isdigit():
        return int(text)

    # Username
    try:
        user = self.vk.users.get(user_ids=text)
        if user:
            return user[0]["id"]
    except Exception:
        pass

    return None
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
        
        self.broadcast_thread = threading.Thread(target=self.broadcast_loop, daemon=True)
        self.broadcast_thread.start()
    
    def load_data(self, filename, default):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_data(filename, default)
            return default
    
    def save_data(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def is_owner(self, user_id):
        return user_id == OWNER_ID
    
    def has_access(self, user_id):
        return self.is_owner(user_id) or user_id in self.access_list
    
    def add_access(self, user_id):
        if user_id not in self.access_list:
            self.access_list.append(user_id)
            self.save_data(ACCESS_FILE, self.access_list)
            return True
        return False
    
    def remove_access(self, user_id):
        if user_id in self.access_list:
            self.access_list.remove(user_id)
            self.save_data(ACCESS_FILE, self.access_list)
            return True
        return False
    
    def add_peer(self, peer_id):
        if peer_id not in self.peers:
            self.peers.append(peer_id)
            self.save_data(PEERS_FILE, self.peers)
            return True
        return False
    
    def remove_peer(self, peer_id):
        if peer_id in self.peers:
            self.peers.remove(peer_id)
            self.save_data(PEERS_FILE, self.peers)
            return True
        return False
    
    def send_message(self, peer_id, text):
        try:
            self.vk.messages.send(
                peer_id=peer_id,
                message=text,
                random_id=get_random_id()
            )
        except Exception as e:
            print(f"Ошибка: {e}")
    
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
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка: {e}")
    
    def broadcast_loop(self):
        while True:
            if self.settings["is_running"] and self.settings["broadcast_text"] and self.peers:
                self.broadcast_message()
            time.sleep(60)
    
    def handle_command(self, message):
        text = message.get('text', '').strip()
        user_id = message['from_id']
        peer_id = message['peer_id']
        
        if not text.startswith('/'):
            return
        
        parts = text.split('\n', 1)
        command = parts[0].lower().strip()
        command_text = parts[1] if len(parts) > 1 else ""
        
        if command == '/+доступ':
            if not self.is_owner(user_id):
               self.send_message(peer_id, "⛔️ Только владелец может выдавать доступ.")
               return

    target_id = self.extract_user_id(message, command_text)

    if not target_id:
        self.send_message(peer_id, "⚠️ Укажите пользователя: ID, @username, ссылку VK, упоминание или перешлите сообщение.")
        return

    if self.add_access(target_id):
        self.send_message(peer_id, f"✅ Доступ выдан пользователю [id{target_id}|пользователь]")
    else:
        self.send_message(peer_id, f"ℹ️ У пользователя [id{target_id}|пользователь] уже есть доступ")
    return
    if command == '/-доступ':
        if not self.is_owner(user_id):
           self.send_message(peer_id, "⛔️ Только владелец может забирать доступ.")
           return

    target_id = self.extract_user_id(message, command_text)

    if not target_id:
        self.send_message(peer_id, "⚠️ Укажите пользователя: ID, @username, ссылку VK, упоминание или перешлите сообщение.")
        return

    if self.remove_access(target_id):
        self.send_message(peer_id, f"✅ Доступ отозван у [id{target_id}|пользователя]")
    else:
        self.send_message(peer_id, f"ℹ️ У [id{target_id}|пользователя] нет доступа")
    return
        
        if command == '/список':
            if not self.is_owner(user_id):
               self.send_message(peer_id, "⛔️ Только владелец может смотреть список.")
               return
            if self.access_list:
                users = "\n".join([f"• {uid}" for uid in self.access_list])
                self.send_message(peer_id, f"📋 Пользователи с доступом:\n{users}")
            else:
                self.send_message(peer_id, "📋 Нет пользователей с доступом.")
            return
        
        if not self.has_access(user_id):
            self.send_message(peer_id, "⛔️ У вас нет доступа к боту.")
            return
        
        if command in ['/чат', '/+чат']:
            if self.add_peer(peer_id):
                self.send_message(peer_id, f"✅ Беседа {peer_id} добавлена.")
            else:
                self.send_message(peer_id, "ℹ️ Уже в базе.")
        
        elif command == '/-чат':
            if self.remove_peer(peer_id):
                self.send_message(peer_id, f"✅ Беседа {peer_id} удалена.")
            else:
                self.send_message(peer_id, "ℹ️ Нет в базе.")
        
        elif command == '/старт':
            if not self.peers:
                self.send_message(peer_id, "⚠️ Нет бесед.")
            elif not self.settings["broadcast_text"]:
                self.send_message(peer_id, "⚠️ Нет текста.")
            else:
                self.settings["is_running"] = True
                self.save_data(SETTINGS_FILE, self.settings)
                self.send_message(peer_id, f"✅ Запущено в {len(self.peers)} бесед.")
        
        elif command == '/стоп':
            self.settings["is_running"] = False
            self.save_data(SETTINGS_FILE, self.settings)
            self.send_message(peer_id, "🛑 Остановлено.")
        
        elif command == '/рассылка':
            if command_text:
                self.settings["broadcast_text"] = command_text.strip()
                self.save_data(SETTINGS_FILE, self.settings)
                self.send_message(peer_id, f"✅ Текст обновлен.")
            else:
                current = self.settings["broadcast_text"] or "Не задан"
                self.send_message(peer_id, f"📄 Текст:\n{current}")
        
        elif command == '/статус':
            status = "✅ Запущена" if self.settings["is_running"] else "🛑 Остановлена"
            self.send_message(peer_id, f"Статус: {status}\nЧатов: {len(self.peers)}\nДоступов: {len(self.access_list)}")
        
        elif command == '/помощь':
            help_text = (
                "📋 Команды:\n"
                "/чат — добавить чат\n"
                "/-чат — удалить чат\n"
                "/старт — запустить\n"
                "/стоп — остановить\n"
                "/рассылка [текст] — задать текст\n"
                "/статус — статус\n"
                "/помощь — помощь\n\n"
                "🔐 Только владелец:\n"
                "/+доступ [ID] — выдать доступ\n"
                "/-доступ [ID] — забрать доступ\n"
                "/список — список доступов"
            )
            self.send_message(peer_id, help_text)
    
    def run(self):
        print("Бот запущен")
        try:
            for event in self.longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.handle_command(event.obj['message'])
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
            self.run()

if __name__ == "__main__":
    bot = PRBot()
    bot.run()
