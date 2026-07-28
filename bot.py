import time
import vk_api
from vk_api.utils import get_random_id

# --- НАСТРОЙКИ ---
# ВСТАВЬ СЮДА НОВЫЙ ТОКЕН (между одинарными кавычками, без скобок!)
VK_TOKEN = 'vk1.a.j7YzvNPaYcJFfVUlTXUDnGeQDH3RVtJCRDIu16DenHlNBqJxBW1p6qJErZMDXRzfy41pVabgENQO8MBlcydzvsYqGepOhfHwnWBzeQ-PShrt2_HrhLQsOEXzUFjhxDAnqG_BNTSaFojr3He5Ctt_sFpmdQYSg-DdI6x--gmY5UpGwWFxXOvbYbs0Mg_ZrhdQNE7kJXAgLrbSWxXkMP7Kmg' 

# ID чата (для беседы: 2000000000 + id беседы)
CHAT_ID = 2000000416

# Текст рассылки
AD_TEXT = "Тест: рассылка работает!"

# Интервал в секундах (минимум 300 для тестов)
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
                random_id=get_random_id()
            )
            print(f"📩 Сообщение отправлено в {time.strftime('%H:%M:%S')}")
            
            # Ждем нужное время
            time.sleep(DELAY_SECONDS)
            
        except vk_api.exceptions.ApiError as e:
            # ИСПРАВЛЕНИЕ: правильный доступ к тексту ошибки
            error_code = e.code
            # Текст ошибки теперь лежит в e.error['error_msg']
            error_msg = e.error.get('error_msg', 'Неизвестная ошибка API')
            
            print(f"💥 Ошибка VK API: {error_code} - {error_msg}")
            
            if error_code == 9: # Flood Control
                print("⚠️ Обнаружен Flood Control. Увеличиваю паузу до 10 минут.")
                time.sleep(600)
            elif error_code == 5: # Invalid Token
                print("💥 КРИТИЧНО: Неверный токен или отозван. Скрипт остановится.")
                break
            elif error_code == 15: # Access Denied
                print("💥 КРИТИЧНО: У бота нет прав на отправку сообщений в этом чате.")
                break
            else:
                time.sleep(60)
                
        except Exception as e:
            print(f"💥 Критическая ошибка скрипта: {e}")
            time.sleep(60)

except Exception as e:
    print(f"💥 Критическая ошибка при старте: {e}")
    print("💡 Подсказка: Чаще всего это неверный токен или отсутствие кавычек.")
