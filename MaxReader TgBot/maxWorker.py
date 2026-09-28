#!/usr/bin/env python3
# maxWorker.py – финальная версия с корректным определением MY_MAX_ID и фильтрацией

import sys
import os
import asyncio
import aiohttp
from pymax import Client
from pymax.auth.providers import SmsCodeProvider, PasswordProvider

# ---------------------- НАСТРОЙКИ ----------------------
if len(sys.argv) < 4:
    print("❌ Ошибка: недостаточно аргументов")
    sys.exit(1)

TG_ID = sys.argv[1]
PHONE_MAX = sys.argv[2]
TG_BOT_URL = f"http://localhost:{sys.argv[3]}/send_to_tg"
WORK_DIR = sys.argv[4] if len(sys.argv) > 4 else "."

print(f"🚀 MAX Worker для {TG_ID} запущен", flush=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ------------------- КЭШ ИМЁН -------------------------
name_cache = {}
MY_MAX_ID = None

# ---------------- КАСТОМНЫЕ ПРОВАЙДЕРЫ -----------------
class FileSmsCodeProvider(SmsCodeProvider):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    async def get_code(self, phone: str) -> str:
        code_file = os.path.join(self.work_dir, "code.txt")
        print(f"📱 Ожидание SMS-кода для {phone}...")
        while not os.path.exists(code_file):
            await asyncio.sleep(0.5)
        with open(code_file, "r", encoding="utf-8") as f:
            code = f.read().strip()
        os.remove(code_file)
        print(f"✅ SMS-код получен")
        return code

class FilePasswordProvider(PasswordProvider):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    async def get_password(self, hint: str | None = None) -> str:
        pwd_file = os.path.join(self.work_dir, "password.txt")
        print(f"🔐 Ожидание 2FA-пароля... (подсказка: {hint})")
        while not os.path.exists(pwd_file):
            await asyncio.sleep(0.5)
        with open(pwd_file, "r", encoding="utf-8") as f:
            password = f.read().strip()
        os.remove(pwd_file)
        if password == "0":
            print("✅ 2FA не требуется")
            return ""
        print("✅ 2FA-пароль получен")
        print(password)
        return password

# ------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -------------------
async def send_to_tg_bot(sender_name: str, sender_id: int, text: str):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "sender_name": sender_name,
                "sender_id": sender_id,
                "receiver_id": int(TG_ID),
                "text": text,
            }
            async with session.post(TG_BOT_URL, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    print(f"✅ Отправлено в Telegram")
                else:
                    print(f"⚠️ Ошибка {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}", flush=True)

async def get_user_name(client_instance, user_id: int) -> str:
    global name_cache
    if user_id in name_cache:
        return name_cache[user_id]
    try:
        if hasattr(client_instance, 'get_user'):
            user = await client_instance.get_user(user_id)
            if user and hasattr(user, 'names') and user.names:
                for name_obj in user.names:
                    if hasattr(name_obj, 'first_name') and name_obj.first_name:
                        name = name_obj.first_name
                        if hasattr(name_obj, 'last_name') and name_obj.last_name:
                            name += f" {name_obj.last_name}"
                        name_cache[user_id] = name
                        return name
    except Exception as e:
        print(f"   get_user ошибка: {e}", flush=True)
    name_cache[user_id] = None
    return None

async def get_my_id(client_instance):
    """Получение своего ID несколькими способами (как в maxReaderDavid.py)"""
    # Способ 1: client.me
    if hasattr(client_instance, 'me') and client_instance.me:
        my_id = getattr(client_instance.me, 'id', None)
        if my_id:
            return my_id
    # Способ 2: client.profile
    if hasattr(client_instance, 'profile') and client_instance.profile:
        my_id = getattr(client_instance.profile, 'id', None)
        if my_id:
            return my_id
    # Способ 3: get_me()
    try:
        if hasattr(client_instance, 'get_me'):
            me = await client_instance.get_me()
            if me:
                my_id = getattr(me, 'id', None)
                if my_id:
                    return my_id
    except Exception as e:
        print(f"   get_me ошибка: {e}", flush=True)
    # Способ 4: поиск по номеру
    try:
        if hasattr(client_instance, 'search_by_phone'):
            result = await client_instance.search_by_phone(PHONE_MAX)
            if result:
                my_id = getattr(result, 'id', None)
                if my_id:
                    return my_id
    except Exception as e:
        print(f"   search_by_phone ошибка: {e}", flush=True)
    return None

# ------------------- ОСНОВНАЯ ЛОГИКА -------------------
async def main():
    global MY_MAX_ID
    print("🔄 Подключение к MAX...", flush=True)
    await send_to_tg_bot("Система", 0, "🔄 Подключаюсь к MAX...")

    # Удаляем прокси
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        os.environ.pop(var, None)

    code_provider = FileSmsCodeProvider(WORK_DIR)
    password_provider = FilePasswordProvider(WORK_DIR)

    client = Client(
        phone=PHONE_MAX,
        work_dir=WORK_DIR,
        session_name="main.db",
        sms_code_provider=code_provider,
        password_provider=password_provider,
    )

    @client.on_start()
    async def on_start(_):
        global MY_MAX_ID
        MY_MAX_ID = await get_my_id(client)
        print(f"\n{'='*50}")
        print(f"✅ MAX клиент запущен")
        print(f"📱 Номер: {PHONE_MAX}")
        print(f"👤 Мой ID: {MY_MAX_ID}")
        print(f"📨 Telegram получатель: {TG_ID}")
        print(f"{'='*50}")
        print(f"📡 Слушаю сообщения...")
        print(f"⚠️ Свои сообщения НЕ пересылаются (ID: {MY_MAX_ID})")
        print(f"{'='*50}\n", flush=True)
        await send_to_tg_bot("Система", 0, "✅ MAX бот успешно запущен!")

    @client.on_message()
    async def on_message(event, _):
        global MY_MAX_ID
        try:
            msg = event.message if hasattr(event, 'message') else event

            # ID отправителя
            sender_id = None
            if hasattr(msg, 'sender'):
                sender_id = msg.sender
            elif hasattr(msg, 'user_id'):
                sender_id = msg.user_id
            elif hasattr(msg, 'from_id'):
                sender_id = msg.from_id

            # Флаг исходящего сообщения (наше)
            is_outgoing = False
            if hasattr(msg, 'out') and msg.out:
                is_outgoing = True
            elif hasattr(msg, 'is_outgoing') and msg.is_outgoing:
                is_outgoing = True

            # Текст
            text = ""
            if hasattr(msg, 'text') and msg.text:
                text = msg.text
            elif hasattr(event, 'text') and event.text:
                text = event.text

            if not text or not text.strip():
                return

            # Фильтрация своих сообщений
            if is_outgoing:
                print(f"\n📨 Исходящее сообщение (своё), не пересылаю: {text[:50]}")
                return
            if MY_MAX_ID and sender_id and sender_id == MY_MAX_ID:
                print(f"\n📨 Сообщение от себя (ID {sender_id}), не пересылаю: {text[:50]}")
                return

            # Если ID своего аккаунта ещё не определён, пробуем ещё раз
            if not MY_MAX_ID:
                MY_MAX_ID = await get_my_id(client)
                if MY_MAX_ID and sender_id == MY_MAX_ID:
                    print(f"\n📨 Своё сообщение (определено позже), не пересылаю")
                    return

            # Имя отправителя
            sender_name = await get_user_name(client, sender_id) if sender_id else "Неизвестно"
            if not sender_name:
                sender_name = f"User_{sender_id}" if sender_id else "Неизвестный"

            print(f"\n📨 Сообщение от {sender_name}: {text[:100]}")
            await send_to_tg_bot(sender_name, sender_id, text)

        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}", flush=True)
            import traceback
            traceback.print_exc()

    try:
        await client.start()
        print("✅ Клиент запущен, ожидаем сообщения...", flush=True)
        await asyncio.Event().wait()
    except Exception as e:
        print(f"❌ Ошибка: {e}", flush=True)
        await send_to_tg_bot("Система", 0, f"❌ Ошибка: {str(e)[:200]}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановлен", flush=True)