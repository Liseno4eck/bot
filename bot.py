import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id
import time
import threading
import json
from datetime import datetime

# Конфигурация
TOKEN = "vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9bme2Cx0UJDKud6S4bysNUO-w"
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

    @staticmethod
    def extract_user_id_from_mention(text):
        """
        Извлекает ID пользователя из упоминания вида [id123|Имя] или [club123|Название]
        Возвращает int ID или None, если не найдено.
        """
        import re
        match = re.search(r'\[id(\d+)\|', text)
        if match:
            return int(match.group(1))
        return None

    def handle_command(self, message):
        text = message.get('text', '').strip()
        user_id = message['from_id']
        peer_id = message['peer_id']

        # Если это реплай (ответ на сообщение) — берём ID из replied_message
        replied_message = message.get('reply_message')
        target_id_from_reply = replied_message['from_id'] if replied_message else None

        if not text.startswith('/'):
            # Если нет команды, но есть реплай и у пользователя есть доступ — можно сделать доп. логику
            return

        parts = text.split('\n', 1)
        command = parts[0].lower().strip()
        command_text = parts[1] if len(parts) > 1 else ""

        # --- Логика выдачи/отзыва доступа ---
        if command in ['/+доступ', '/-доступ']:
            if not self.is_owner(user_id):
                self.send_message(peer_id, "⛔️ Только владелец может выдавать/отзывать доступ.")
                return

            action = 'add' if command == '/+доступ' else 'remove'
            target_id = None

            # Вариант 1: реплай на сообщение
            if target_id_from_reply is not None:
                target_id = target_id_from_reply

            # Вариант 2: упоминание в тексте [id123|...]
            if target_id is None:
                mentioned_id = self.extract_user_id_from_mention(command_text)
                if mentioned_id:
                    target_id = mentioned_id

            # Вариант 3: просто числовой ID в тексте
            if target_id is None and command_text.strip():
                try:
                    target_id = int(command_text.strip())
                except ValueError:
                    pass

            if target_id is None:
                self.send_message(peer_id, "⚠️ Укажите ID пользователя: числом, через упоминание или ответом на его сообщение.")
                return

            if action == 'add':
                if self.add_access(target_id):
                    self.send_message(peer_id, f"✅ Доступ выдан пользователю {target_id}")
                else:
                    self.send_message(peer_id, f"ℹ️ У пользователя {target_id} уже есть доступ.")
            else:
                if self.remove_access(target_id):
                    self.send_message(peer_id, f"✅ Доступ отозван у пользователя {target_id}")
                else:
                    self.send_message(peer_id, f"ℹ️ У пользователя {target_id} нет доступа.")
            return

        elif command == '/список':
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
                self.send_message(peer_id, f"✅ Текст обновлён.")
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
                "/старт — запустить рассылку\n"
                "/стоп — остановить рассылку\n"
                "/рассылка [текст] — задать текст рассылки\n"
                "/статус — статус бота\n"
                "/помощь — помощь\n\n"
                "🔐 Только владелец:\n"
                "/+доступ [ID / @упоминание / ответ на смс] — выдать доступ\n"
                "/-доступ [ID / @упоминание / ответ на смс] — забрать доступ\n"
                "/список — список пользователей с доступом"
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
