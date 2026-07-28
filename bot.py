import time
import vk_api
from vk_api.utils import get_random_id

# --- НАСТРОЙКИ ---
# ВСТАВЬТЕ СЮДА НОВЫЙ ТОКЕН (старый не используйте!)
VK_TOKEN = 'vk1.a.j7YzvNPaYcJFfVUlTXUDnGeQDH3RVtJCRDIu16DenHlNBqJxBW1p6qJErZMDXRzfy41pVabgENQO8MBlcydzvsYqGepOhfHwnWBzeQ-PShrt2_HrhLQsOEXzUFjhxDAnqG_BNTSaFojr3He5Ctt_sFpmdQYSg-DdI6x--gmY5UpGwWFxXOvbYbs0Mg_ZrhdQNE7kJXAgLrbSWxXkMP7Kmg' 

# ID чата (из вашего запроса)
# Для личных сообщений (ЛС) это ID пользователя (число). 
# Для беседы это peer_id = 2000000000 + id беседы. 
# У тебя сейчас стоит 2000000416 — это ID беседы.
CHAT_ID = 2000000416

# Текст рассылки
AD_TEXT = "Тест: рассылка работает!"

# Интервал в секундах.
# ВАЖНО: Для тестов ставь минимум 300 сек (5 минут).
# Если ставить 60 сек, ВК почти гарантированно выдаст бан по Flood Control (ошибка 9).
DELAY_SECONDS = 300

print("🚀 ЗАПУСК СКРИПТА РАССЫЛКИ...")
print(f"🎯 Цель: чат ID {CHAT_ID}")
print(f"⏳ Интервал: {DELAY_SECONDS} сек")

try:
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    print("✅ Авторизация успешна. Начинаю цикл рассылки...")

    while True:
        try:
            # Отправляем сообщение
            vk.messages.send(
                peer_id=CHAT_ID,
                message=AD_TEXT,
                random_id=get_random_id() # Обязательно для уникальности сообщений
            )
            print(f"📩 Сообщение отправлено в {time.strftime('%H:%M:%S')}")
            
            # Ждем нужное время
            time.sleep(DELAY_SECONDS)
            
        except vk_api.exceptions.ApiError as e:
            error_code = e.code
            error_msg = e.error_msg
            print(f"💥 Ошибка VK API: {error_code} - {error_msg}")
            
            if error_code == 9: # Flood Control
                print("⚠️ Обнаружен Flood Control. Увеличиваю паузу до 10 минут, чтобы не получить бан.")
                time.sleep(600)
            else:
                # Для других ошибок (например, неверный токен) лучше остановиться или спать долго
                time.sleep(60)
                
        except Exception as e:
            print(f"💥 Критическая ошибка скрипта: {e}")
            time.sleep(60)

except Exception as e:
    print(f"💥 Критическая ошибка при старте: {e}")
