import vk_api
from vk_api.utils import get_random_id

VK_TOKEN = 'vk1.a.baBit_arE7XyBbqXVkUrUYKMqCOw2zAZJ5_ZiFTyyW2hblfgfj0xadnRuTLIJSpa7G58feIA1p-UIt5ysnef1gwh4u78K3vV51Wc5IBmPLOJ5JyTO49wzxoWL1tMwtg5AQgC4QhV7Ka4tAJXgbqgVp75gQ39T11_72y4ZYiuTCgv36Sw8nrvcxOKPxcrW9Bme2Cx0UJDKud6S4bysNUO-w'

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

*Отправляем в ЛС сообщества (id = -240350664)*
vk.messages.send(peer_id=-240350664, message='Тест', random_id=get_random_id())
print("Отправлено в ЛС")
