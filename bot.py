import vk_api
from vk_api.utils import get_random_id
import time

VK_TOKEN = 'vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9Bme2Cx0UJDKud6S4bysNUO-w'
GROUP_ID = 240350664

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

print("Запустите этот код, затем добавьте бота в чат через кнопку 'Добавить в чат'")

*Ждём 30 секунд, чтобы вы успели добавить бота*
time.sleep(30)

*Пытаемся получить список диалогов*
try:
    conversations = vk.messages.getConversations(filter='all', count=200)
    print(f"Всего диалогов: {len(conversations['items'])}")
    for item in conversations['items']:
        peer = item['conversation']['peer']
        print(f"ID: {peer['id']}, Тип: {peer['type']}")
except Exception as e:
    print(f"Ошибка: {e}")
