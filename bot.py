import time
import vk_api
from vk_api.utils import get_random_id

# ================= НАСТРОЙКИ =================
# ВСТАВЬТЕ СЮДА ТОЛЬКО НОВЫЙ ТОКЕН (старый не используйте!)
# Формат должен быть таким: vk1.a.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
VK_TOKEN = 'vk1.a.JX1jCRFp175La53q0TKHQSUjo58HjZMZoZtMzvHyWsaNbw-idR02oN2wjE60T-w3J2Ou8f5FPkKBckH_qtjWrTTqK9-NYI4KzvTY4-cqqnoGWmwUzCu6zCpcJ4I20DbNW2XrLmDNsuTfRAie24rfkPTGubtf3Qk-976CJSuRqC7hyjVRIcg1ZRpjZp1CO1lf9z2peUkHDp1KHDu-v3S78g'

# ID чата (из вашего запроса)
CHAT_ID = 2000000416

# Текст, который нужно пиарить. Можете менять на любой другой.
# Сюда можно вставить то, что вы планировали написать.
AD_TEXT = "тест, работет"

# Интервал в секундах. 
# ВАЖНО: Для тестов ставьте минимум 300 сек (5 минут). 
# Раз в минуту (60 сек) ВК часто дает бан по Flood Control (ошибка 9).
DELAY_SECONDS = 300 
# =============================================

def send_ad_message():
    try:
        # Инициализация сессии
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
        
        print(f"Попытка отправки в чат {CHAT_ID}...")
        
        # Отправка сообщения
        # Используем chat_id для старых ID бесед. 
        # Если будет ошибка, раскомментируйте блок ниже с peer_id.
        response = vk.messages.send(
            chat_id=CHAT_ID,
            message=AD_TEXT,
            random_id=get_random_id()  # Критически важно для уникальности запроса
        )
        
        print(f"✅ Сообщение успешно отправлено! ID сообщения: {response}")
        
    except vk_api.exceptions.ApiError as e:
        error_code = e.code
        error_msg = e.error.get('error_msg', 'Неизвестная ошибка')
        print(f"❌ Ошибка API VK: Код {error_code} - {error_msg}")
        
        if error_code == 9:
            print("⚠️ Это Flood Control (слишком частые запросы). Увеличьте DELAY_SECONDS!")
        elif error_code == 15:
            print("⚠️ Ошибка 15: Нет прав на отправку сообщений. Проверьте, что бот - админ чата.")
        elif error_code == 5:
            print("⚠️ Ошибка 5: Неверный токен. Проверьте строку VK_TOKEN.")
            
    except Exception as e:
        print(f"❌ Общая ошибка Python: {e}")

def main():
    print("🤖 Бот запущен. Ожидание первого цикла...")
    while True:
        send_ad_message()
        print(f"⏳ Ожидание {DELAY_SECONDS} секунд до следующей отправки...\n")
        time.sleep(DELAY_SECONDS)

if __name__ == '__main__':
    main()
