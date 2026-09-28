import os
import re
import json
import time
import threading

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id

# ---------- Конфигурация (берётся из переменных окружения хостинга) ----------
TOKEN = os.getenv("TOKEN") or os.getenv("VK_TOKEN")
if not TOKEN:
    raise RuntimeError("Не задана переменная окружения TOKEN (токен сообщества VK)")

GROUP_ID = int(os.getenv("GROUP_ID", "240350664"))
OWNER_ID = int(os.getenv("OWNER_ID", "875762552"))

# Папка для хранения данных. Если на хостинге есть постоянный диск/том,
# укажите путь к нему в переменной DATA_DIR, чтобы файлы не пропадали при перезапуске.
DATA_DIR = os.getenv("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)

PEERS_FILE = os.path.join(DATA_DIR, "peers.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ACCESS_FILE = os.path.join(DATA_DIR, "access.json")

BROADCAST_INTERVAL = 3600  # секунд между рассылками

DEFAULT_SETTINGS = {
    "broadcast_text": "",
    "is_running": False,
    "owner_id": OWNER_ID,
    "last_broadcast": 0,
}


class PRBot:
    def __init__(self):
        self.lock = threading.Lock()

        self.vk_session = vk_api.VkApi(token=TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, GROUP_ID)

        self.peers = self.load_data(PEERS_FILE, [])
        self.settings = self.load_data(SETTINGS_FILE, dict(DEFAULT_SETTINGS))
        self.access_list = self.load_data(ACCESS_FILE, [])

        if not isinstance(self.peers, list):
            self.peers = []
            self.save_data(PEERS_FILE, self.peers)
        if not isinstance(self.access_list, list):
            self.access_list = []
            self.save_data(ACCESS_FILE, self.access_list)
        if not isinstance(self.settings, dict):
            self.settings = dict(DEFAULT_SETTINGS)

        # Дополняем настройки недостающими ключами (если файл старый)
        for key, value in DEFAULT_SETTINGS.items():
            self.settings.setdefault(key, value)
        self.save_data(SETTINGS_FILE, self.settings)

        print(f"Загружено бесед: {len(self.peers)}, доступов: {len(self.access_list)}")

        self.broadcast_thread = threading.Thread(target=self.broadcast_loop, daemon=True)
        self.broadcast_thread.start()

    # ---------- Работа с файлами ----------
    def load_data(self, filename, default):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_data(filename, default)
            return default

    def save_data(self, filename, data):
        # Атомарная запись: сначала во временный файл, потом замена,
        # чтобы файл не повредился, если бота остановят посреди записи
        tmp = filename + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filename)

    # ---------- Права ----------
    def is_owner(self, user_id):
        return user_id == OWNER_ID

    def has_access(self, user_id):
        return self.is_owner(user_id) or user_id in self.access_list

    def add_access(self, user_id):
        with self.lock:
            if user_id not in self.access_list:
                self.access_list.append(user_id)
                self.save_data(ACCESS_FILE, self.access_list)
                return True
            return False

    def remove_access(self, user_id):
        with self.lock:
            if user_id in self.access_list:
                self.access_list.remove(user_id)
                self.save_data(ACCESS_FILE, self.access_list)
                return True
            return False

    # ---------- Чаты ----------
    def add_peer(self, peer_id):
        with self.lock:
            if peer_id not in self.peers:
                self.peers.append(peer_id)
                self.save_data(PEERS_FILE, self.peers)
                return True
            return False

    def remove_peer(self, peer_id):
        with self.lock:
            if peer_id in self.peers:
                self.peers.remove(peer_id)
                self.save_data(PEERS_FILE, self.peers)
                return True
            return False

    def save_settings(self):
        with self.lock:
            self.save_data(SETTINGS_FILE, self.settings)

    # ---------- Определение пользователя ----------
    def extract_user_id(self, message, text):
        # Пересланное сообщение
        fwd = message.get("fwd_messages", [])
        if fwd:
            return fwd[0].get("from_id")

        # Упоминание [id123|Имя]
        match = re.search(r"\[id(\d+)\|", text)
        if match:
            return int(match.group(1))

        clean_text = text.strip().replace("@", "")
        clean_text = clean_text.replace("https://vk.com/", "").replace("http://vk.com/", "")

        # Числовой ID
        if clean_text.isdigit():
            return int(clean_text)

        # Короткое имя (username)
        if clean_text:
            try:
                user = self.vk.users.get(user_ids=clean_text)
                if user:
                    return user[0]["id"]
            except Exception:
                pass

        return None

    # ---------- Отправка ----------
    def send_message(self, peer_id, text):
        try:
            self.vk.messages.send(
                peer_id=peer_id,
                message=text,
                random_id=get_random_id()
            )
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def broadcast_message(self):
        if not self.settings["broadcast_text"]:
            return
        for peer_id in list(self.peers):
            try:
                self.vk.messages.send(
                    peer_id=peer_id,
                    message=self.settings["broadcast_text"],
                    random_id=get_random_id()
                )
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка рассылки в чат {peer_id}: {e}")

    def broadcast_loop(self):
        while True:
            try:
                if (self.settings["is_running"]
                        and self.settings["broadcast_text"]
                        and self.peers
                        and time.time() - self.settings.get("last_broadcast", 0) >= BROADCAST_INTERVAL):
                    self.broadcast_message()
                    self.settings["last_broadcast"] = time.time()
                    self.save_settings()
            except Exception as e:
                print(f"Ошибка в цикле рассылки: {e}")
            time.sleep(30)

    # ---------- Команды ----------
    def handle_command(self, message):
        text = message.get('text', '').strip()
        user_id = message['from_id']
        peer_id = message['peer_id']

        if not text.startswith('/'):
            return

        # Нет доступа — полностью игнорируем, ничего не отвечаем
        if not self.has_access(user_id):
            return

        parts = text.split('\n', 1)
        command = parts[0].lower().strip()
        command_text = parts[1] if len(parts) > 1 else ""

        # Выдача доступа — может любой, у кого есть доступ
        if command == '/+доступ':
            target_id = self.extract_user_id(message, command_text)
            if not target_id:
                self.send_message(peer_id, "⚠️ Укажите пользователя: ID, @username, ссылку VK, упоминание или перешлите сообщение.")
                return

            if self.add_access(target_id):
                self.send_message(peer_id, f"✅ Доступ выдан пользователю [id{target_id}|пользователь]")
            else:
                self.send_message(peer_id, f"ℹ️ У пользователя [id{target_id}|пользователь] уже есть доступ")
            return

        # Забрать доступ и посмотреть список — только владелец (для остальных тишина)
        if command == '/-доступ':
            if not self.is_owner(user_id):
                return

            target_id = self.extract_user_id(message, command_text)
            if not target_id:
                self.send_message(peer_id, "⚠️ Укажите пользователя: ID, @username, ссылку VK, упоминание или перешлите сообщение.")
                return

            if self.is_owner(target_id):
                self.send_message(peer_id, "⚠️ Нельзя забрать доступ у владельца.")
                return

            if self.remove_access(target_id):
                self.send_message(peer_id, f"✅ Доступ отозван у [id{target_id}|пользователя]")
            else:
                self.send_message(peer_id, f"ℹ️ У [id{target_id}|пользователя] нет доступа")
            return

        if command == '/список':
            if not self.is_owner(user_id):
                return
            if self.access_list:
                users = "\n".join([f"• {uid}" for uid in self.access_list])
                self.send_message(peer_id, f"📋 Пользователи с доступом:\n{users}")
            else:
                self.send_message(peer_id, "📋 Нет пользователей с доступом.")
            return

        # Добавление/удаление чата
        if command in ['/чат', '/+чат']:
            if self.add_peer(peer_id):
                self.send_message(peer_id, f"✅ Беседа {peer_id} добавлена.")
            else:
                self.send_message(peer_id, "ℹ️ Уже в базе.")
            return

        if command == '/-чат':
            if self.remove_peer(peer_id):
                self.send_message(peer_id, f"✅ Беседа {peer_id} удалена.")
            else:
                self.send_message(peer_id, "ℹ️ Нет в базе.")
            return

        # Управление рассылкой
        if command == '/старт':
            if not self.peers:
                self.send_message(peer_id, "⚠️ Нет бесед.")
                return
            if not self.settings["broadcast_text"]:
                self.send_message(peer_id, "⚠️ Нет текста.")
                return
            self.settings["is_running"] = True
            self.save_settings()
            self.send_message(peer_id, f"✅ Запущено в {len(self.peers)} бесед.")
            return

        if command == '/стоп':
            self.settings["is_running"] = False
            self.save_settings()
            self.send_message(peer_id, "🛑 Остановлено.")
            return

        if command == '/рассылка':
            if command_text:
                self.settings["broadcast_text"] = command_text.strip()
                self.save_settings()
                self.send_message(peer_id, "✅ Текст обновлён.")
            else:
                current = self.settings["broadcast_text"] or "Не задан"
                self.send_message(peer_id, f"📄 Текст:\n{current}")
            return

        if command == '/статус':
            status = "✅ Запущена" if self.settings["is_running"] else "🛑 Остановлена"
            self.send_message(peer_id, f"Статус: {status}\nЧатов: {len(self.peers)}\nДоступов: {len(self.access_list)}")
            return

        if command == '/помощь':
            help_text = (
                "📋 Команды:\n"
                "/+чат — добавить чат\n"
                "/-чат — удалить чат\n"
                "/старт — запустить рассылку\n"
                "/стоп — остановить рассылку\n"
                "/рассылка [текст] — задать текст рассылки\n"
                "/статус — статус бота\n"
                "/+доступ [ID] — выдать доступ\n"
                "/помощь — помощь\n\n"
                "🔐 Только владелец:\n"
                "/-доступ [ID] — забрать доступ\n"
                "/список — список пользователей с доступом"
            )
            self.send_message(peer_id, help_text)
            return

    def run(self):
        print("Бот запущен")
        while True:
            try:
                for event in self.longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        self.handle_command(event.obj['message'])
            except Exception as e:
                print(f"Ошибка longpoll: {e}")
                time.sleep(5)


if __name__ == "__main__":
    bot = PRBot()
    bot.run()
