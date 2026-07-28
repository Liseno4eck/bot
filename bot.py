import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import time
from threading import Thread

VK_TOKEN = 'vk1.a.j7YzvNPaYcJFfVUlTXUDnGeQDH3RVtJCRDIu16DenHlNBqJxBW1p6qJErZMDXRzfy41pVabgENQO8MBlcydzvsYqGepOhfHwnWBzeQ-PShrt2_HrhLQsOEXzUFjhxDAnqG_BNTSaFojr3He5Ctt_sFpmdQYSg-DdI6x--gmY5UpGwWFxXOvbYbs0Mg_ZrhdQNE7kJXAgLrbSWxXkMP7Kmg'  # права: messages

MY_TEXT = """🔥 Пиар-сообщение! 🔥
Заходи в наше сообщество: vk.com/club123456789
Будем рады видеть тебя! 😊"""

INTERVAL = 300  # 1 час

vk_session = vk_api.VkApi(token=VK_TOKEN)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

*Список чатов, где запущен пиар*
active_chats = {}

def pr_sender(chat_id):
    while chat_id in active_chats and active_chats[chat_id]:
        try:
            vk.messages.send(
                peer_id=chat_id,
                message=MY_TEXT,
                random_id=get_random_id()
            )
            print(f"Пиар отправлен в чат {chat_id} в {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Ошибка в чате {chat_id}: {e}")
            break
        time.sleep(INTERVAL)

print("Бот запущен. Жду команду !пиар...")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        peer_id = event.peer_id
        
        # Проверяем, что это чат (peer_id > 2000000000)
        if peer_id > 2000000000 and event.text.strip().lower() == '!пиар':
            if peer_id in active_chats and active_chats[peer_id]:
                vk.messages.send(
                    peer_id=peer_id,
                    message="⚠️ Пиар уже запущен в этом чате",
                    random_id=get_random_id()
                )
            else:
                active_chats[peer_id] = True
                thread = Thread(target=pr_sender, args=(peer_id,))
                thread.daemon = True
                thread.start()
                vk.messages.send(
                    peer_id=peer_id,
                    message="✅ Пиар запущен! Буду писать раз в час",
                    random_id=get_random_id()
                )
