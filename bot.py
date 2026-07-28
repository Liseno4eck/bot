import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import time
from threading import Thread

VK_TOKEN = 'vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9Bme2Cx0UJDKud6S4bysNUO-w'
GROUP_ID = 240350664

MY_TEXT = "работает"
INTERVAL = 300

vk_session = vk_api.VkApi(token=VK_TOKEN)
longpoll = VkLongPoll(vk_session, group_id=GROUP_ID)
vk = vk_session.get_api()

active_chats = {}

def pr_sender(chat_id):
    while chat_id in active_chats and active_chats[chat_id]:
        try:
            vk.messages.send(peer_id=chat_id, message=MY_TEXT, random_id=get_random_id())
            print(f"Пиар отправлен в чат {chat_id} в {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Ошибка в чате {chat_id}: {e}")
            break
        time.sleep(INTERVAL)

print("Бот запущен. Добавьте бота в чат и напишите !пиар")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        peer_id = event.peer_id
        
        # Если сообщение из беседы (peer_id > 2000000000)
        if peer_id > 2000000000 and event.text.strip().lower() == '!пиар':
            if peer_id in active_chats and active_chats[peer_id]:
                vk.messages.send(peer_id=peer_id, message="⚠️ Пиар уже запущен", random_id=get_random_id())
            else:
                active_chats[peer_id] = True
                thread = Thread(target=pr_sender, args=(peer_id,))
                thread.daemon = True
                thread.start()
                vk.messages.send(peer_id=peer_id, message="✅ ПИАР АКТИВИРОВАН", random_id=get_random_id())
                print(f"Пиар активирован в чате {peer_id}")
