import vk_api
from vk_api.utils import get_random_id

VK_TOKEN = 'vk1.a.j7YzvNPaYcJFfVUlTXUDnGeQDH3RVtJCRDIu16DenHlNBqJxBW1p6qJErZMDXRzfy41pVabgENQO8MBlcydzvsYqGepOhfHwnWBzeQ-PShrt2_HrhLQsOEXzUFjhxDAnqG_BNTSaFojr3He5Ctt_sFpmdQYSg-DdI6x--gmY5UpGwWFxXOvbYbs0Mg_ZrhdQNE7kJXAgLrbSWxXkMP7Kmg'
CHAT_ID = 2000000419  # замените на ID вашей беседы

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

vk.messages.send(
    peer_id=CHAT_ID,
    message='Тест',
    random_id=get_random_id()
)
print("Отправлено")
