import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import time
import threading
import json
from datetime import datetime

# Конфигурация
TOKEN = "vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9Bme2Cx0UJDKud6S4bysNUO-w"
GROUP_ID = 2000000419
OWNER_ID = 875762552  # ID владельца бота, замените на свой или оставьте None

# Файлы для хранения данных
PEERS_FILE = "peers.json"
SETTINGS_FILE = "settings.json"

class PRBot:
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, GROUP_ID)
        
        # Загружаем данные
        self.peers = self.load_data(PEERS_FILE, [])
        self.settings = self.load_data(SETTINGS_FILE, {
            "broadcast_text": "",
            "is_running": False,
            "owner_id": OWNER_ID
        })
        
        # Проверяем, что peers - это список
        if not isinstance(self.peers, list):
            print(f"Внимание: peers.json содержит не список, а {type(self.peers)}. Сбрасываю в пустой список.")
            self.peers = []
            self.save_data(PEERS_FILE, self.peers)
        
        # Запускаем рассылку в отдельном потоке
        self.broadcast_thread = threading.Thread(target=self.broadcast_loop, daemon=True)
        self.broadcast_thread.start()
    
    def load_data(self, filename, default):
        """Загрузка данных из JSON файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.save_data(filename, default)
            return default
        except json.JSONDecodeError:
            print(f"Ошибка чтения {filename}. Использую значения по умолчанию.")
            self.save_data(filename, default)
            return default
    
    def save_data(self, filename, data):
        """Сохранение данных в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def is_owner(self, user_id):
        """Проверка, является ли пользователь владельцем бота"""
        if self.settings["owner_id"] is None:
            self.settings["owner_id"] = user_id
            self.save_data(SETTINGS_FILE, self.settings)
            return True
        return user_id == self.settings["owner_id"]
    
    def add_peer(self, peer_id):
        """Добавление беседы в базу данных"""
        if peer_id not in self.peers:
            self.peers.append(peer_id)
            self.save_data(PEERS_FILE, self.peers)
            return True
        return False
    
    def remove_peer(self, peer_id):
        """Удаление беседы из базы данных"""
        if peer_id in self.peers:
            self.peers.remove(peer_id)
            self.save_data(PEERS_FILE, self.peers)
            return True
        return False
    
    def send_message(self, peer_id, text):
        """Отправка сообщения"""
        try:
            self.vk.messages.send(
                peer_id=peer_id,
                message=text,
                random_id=0
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
    
    def broadcast_message(self):
        """Рассылка сообщения по всем беседам"""
        if not self.settings["broadcast_text"]:
            return
        
        print(f"[{datetime.now()}] Начинаю рассылку в {len(self.peers)} бесед")
        
        for peer_id in self.peers:
            try:
                self.vk.messages.send(
                    peer_id=peer_id,
                    message=self.settings["broadcast_text"],
                    random_id=0
                )
                print(f"[{datetime.now()}] Рассылка отправлена в беседу {peer_id}")
                time.sleep(1)  # Задержка между отправками
            except Exception as e:
                print(f"Ошибка при отправке в беседу {peer_id}: {e}")
    
    def broadcast_loop(self):
        """Цикл рассылки"""
        while True:
            if self.settings["is_running"] and self.settings["broadcast_text"] and self.peers:
                self.broadcast_message()
            time.sleep(600)  # 10 минут
    
    def handle_command(self, message):
        """Обработка команд"""
        text = message.get('text', '').strip()
        user_id = message['from_id']
        peer_id = message['peer_id']
        
        # Проверяем, начинается ли сообщение с /
        if not text.startswith('/'):
            return
        
        # Разбираем команду
        parts = text.split('\n', 1)
        command = parts[0].lower().strip()
        command_text = parts[1] if len(parts) > 1 else ""
        
        # Проверяем права владельца
        if not self.is_owner(user_id):
            self.send_message(peer_id, "⛔ У вас нет прав для выполнения команд.")
            return
        
        # Обработка команд
        if command == '/чат' or command == '/+чат':
            if self.add_peer(peer_id):
                self.send_message(peer_id, f"✅ Беседа {peer_id} добавлена в базу данных.")
                print(f"Добавлена беседа {peer_id}, всего бесед: {len(self.peers)}")
            else:
                self.send_message(peer_id, "ℹ️ Эта беседа уже есть в базе данных.")
        
        elif command == '/-чат':
            if self.remove_peer(peer_id):
                self.send_message(peer_id, f"✅ Беседа {peer_id} удалена из базы данных.")
                print(f"Удалена беседа {peer_id}, осталось бесед: {len(self.peers)}")
            else:
                self.send_message(peer_id, "ℹ️ Этой беседы нет в базе данных.")
        
        elif command == '/старт':
            if not self.peers:
                self.send_message(peer_id, "⚠️ Нет добавленных бесед для рассылки.")
            elif not self.settings["broadcast_text"]:
                self.send_message(peer_id, "⚠️ Не задан текст рассылки. Используйте /рассылка")
            else:
                self.settings["is_running"] = True
                self.save_data(SETTINGS_FILE, self.settings)
                # Сразу отправляем рассылку
                self.broadcast_message()
                self.send_message(peer_id, f"✅ Рассылка запущена и отправлена в {len(self.peers)} бесед!")
                print("Рассылка запущена")
        
        elif command == '/стоп':
            if self.settings["is_running"]:
                self.settings["is_running"] = False
                self.save_data(SETTINGS_FILE, self.settings)
                self.send_message(peer_id, "🛑 Рассылка остановлена.")
                print("Рассылка остановлена")
            else:
                self.send_message(peer_id, "ℹ️ Рассылка уже остановлена.")
        
        elif command == '/помощь':
            help_text = (
                "📋 Доступные команды:\n\n"
                "/чат или /+чат — добавить беседу в базу\n"
                "/-чат — удалить беседу из базы\n"
                "/старт — запустить рассылку\n"
                "/стоп — остановить рассылку\n"
                "/рассылка [текст] — задать/изменить текст рассылки\n"
                "/статус — показать текущий статус\n"
                "/помощь — показать это сообщение"
            )
            self.send_message(peer_id, help_text)
        
        elif command == '/статус':
            status = "✅ Запущена" if self.settings["is_running"] else "🛑 Остановлена"
            current_text = self.settings["broadcast_text"] if self.settings["broadcast_text"] else "Не задан"
            status_text = (
                f"📊 Статус бота:\n\n"
                f"🔄 Статус рассылки: {status}\n"
                f"💬 Количество бесед: {len(self.peers)}\n"
                f"📝 Текст рассылки:\n{current_text}\n\n"
                f"⏰ Интервал рассылки: 10 минут"
            )
            self.send_message(peer_id, status_text)
        
        elif command == '/рассылка':
            if command_text:
                # Устанавливаем новый текст рассылки
                self.settings["broadcast_text"] = command_text.strip()
                self.settings["is_running"] = True
                self.save_data(SETTINGS_FILE, self.settings)
                self.send_message(peer_id, f"✅ Текст рассылки обновлен и запущен:\n\n{command_text}")
                print("Текст рассылки обновлен")
            else:
                # Показываем текущий текст
                current_text = self.settings["broadcast_text"] if self.settings["broadcast_text"] else "Не задан"
                status = "Запущена" if self.settings["is_running"] else "Остановлена"
                self.send_message(peer_id, 
                    f"📊 Статус рассылки: {status}\n"
                    f"📝 Количество бесед: {len(self.peers)}\n"
                    f"📄 Текущий текст:\n\n{current_text}\n\n"
                    f"Для изменения используйте:\n"
                    f"/рассылка\n"
                    f"[ваш текст]")
    
    def run(self):
        """Запуск бота"""
        print("Бот запущен и ожидает команды...")
        print(f"ID группы: {GROUP_ID}")
        
        try:
            for event in self.longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.obj['message']
                    self.handle_command(message)
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(5)
            self.run()

if __name__ == "__main__":
    # Установите ваш ID ВКонтакте
    OWNER_ID = 875762552  # Замените на ваш ID, например: 123456789
    
    bot = PRBot()
    bot.run()
