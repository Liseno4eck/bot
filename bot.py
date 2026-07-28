import time
import vk_api
from vk_api.utils import get_random_id

# --- НАСТРОЙКИ ---
VK_TOKEN = 'vk1.a.j7YzvNPaYcJFfVUlTXUDnGeQDH3RVtJCRDIu16DenHlNBqJxBW1p6qJErZMDXRzfy41pVabgENQO8MBlcydzvsYqGepOhfHwnWBzeQ-PShrt2_HrhLQsOEXzUFjhxDAnqG_BNTSaFojr3He5Ctt_sFpmdQYSg-DdI6x--gmY5UpGwWFxXOvbYbs0Mg_ZrhdQNE7kJXAgLrbSWxXkMP7Kmg'  # вставь сюда токен сообщества (не пользователя!)
OWNER_ID = -240350664               # ID сообщества с минусом (например, -123456789)
POST_TEXT = "Тест: работет"

# Инициализация VK API
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

def post_to_wall():
    try:
        vk.wall.post(
            owner_id=OWNER_ID,
            message=POST_TEXT,
            random_id=get_random_id()
        )
        print("Пост опубликован.")
    except Exception as e:
        print(f"Ошибка при публикации: {e}")

if __name__ == "__main__":
    print("Бот запущен. Пост будет публиковаться раз в час.")
    while True:
        post_to_wall()
        time.sleep(3600)  # 3600 секунд = 1 час
