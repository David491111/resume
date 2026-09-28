# tgBot.py - PTY версия с анализом вывода
import asyncio
import json
import os
import sys
import pty
import shutil
import signal
from datetime import datetime
from aiohttp import web
from telethon import TelegramClient, events
from telethon.network.connection import ConnectionTcpMTProxyRandomizedIntermediate
import os
from dotenv import load_dotenv

# ===== НАСТРОЙКИ =====

load_dotenv()
API_ID = 39475867
API_HASH = "bac6f73849988dfa3f1b0afdf88d9986"
TG_BOT_TOKEN = "8890133083:AAFwn-rXJKwU7bXs0P3HB3pcBcEnE5T_AGc"
HTTP_PORT = 8080
USE_PROXY = True
PROXY_HOST = os.getenv("PROXY_HOST")
print(PROXY_HOST)
PROXY_PORT = int(os.getenv("PROXY_PORT","1443"))
PROXY_SECRET = os.getenv("PROXY_SECRET")
# =======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
MAX_WORKER_SCRIPT = os.path.join(BASE_DIR, "maxWorker.py")

os.makedirs(CACHE_DIR, exist_ok=True)

users = {}
processes = {}
pending_auth = {}
stdin_writer = {}

def get_telegram_client():
    session_file = os.path.join(CACHE_DIR, "tg_bot")
    if USE_PROXY:
        return TelegramClient(
            session_file, API_ID, API_HASH,
            connection=ConnectionTcpMTProxyRandomizedIntermediate,
            proxy=(PROXY_HOST, PROXY_PORT, PROXY_SECRET),
            connection_retries=5
        )
    return TelegramClient(session_file, API_ID, API_HASH)

tg_client = get_telegram_client()

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        print(f"📚 Загружено {len(users)} пользователей")

def save_users():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    print(f"💾 Сохранено {len(users)} пользователей")

async def start_max_worker(tg_id: str, phone: str):
    try:
        user_cache_dir = os.path.join(CACHE_DIR, f"user_{tg_id}")
        os.makedirs(user_cache_dir, exist_ok=True)

        if tg_id in processes:
            old = processes[tg_id]['proc']
            if old.returncode is None:
                old.terminate()
                try:
                    await asyncio.wait_for(asyncio.to_thread(old.wait), timeout=5)
                except asyncio.TimeoutError:
                    old.kill()
            if 'master_fd' in processes[tg_id]:
                try:
                    os.close(processes[tg_id]['master_fd'])
                except OSError:
                    pass
            del processes[tg_id]
            if tg_id in stdin_writer:
                del stdin_writer[tg_id]

        master_fd, slave_fd = pty.openpty()
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUNBUFFERED'] = '1'
        for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            env.pop(var, None)

        process = await asyncio.create_subprocess_exec(
            sys.executable, '-u', MAX_WORKER_SCRIPT, tg_id, phone, str(HTTP_PORT), user_cache_dir,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=env,
            pass_fds=(slave_fd,)
        )
        os.close(slave_fd)

        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        transport, _ = await loop.connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(reader),
            os.fdopen(master_fd, 'rb', buffering=0)
        )
        writer = os.fdopen(master_fd, 'wb', buffering=0)

        processes[tg_id] = {
            'proc': process,
            'master_fd': master_fd,
            'reader': reader,
            'transport': transport,
        }
        stdin_writer[tg_id] = writer
        print(f"✅ Запущен Worker для {tg_id} (PID: {process.pid}) через PTY")

        asyncio.create_task(read_worker_output(tg_id, reader, process))
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

async def read_worker_output(tg_id: str, reader: asyncio.StreamReader, process):
    buffer = bytearray()
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                if process.returncode is not None:
                    break
                await asyncio.sleep(0.1)
                continue
            buffer.extend(data)
            while b'\n' in buffer:
                line_bytes, buffer = buffer.split(b'\n', 1)
                line = line_bytes.decode('utf-8', errors='replace').strip()
                if not line:
                    continue
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"\n[→] [{timestamp}] [{tg_id}] {line}")

                if "requesting sms code" in line.lower():
                    pending_auth[tg_id] = {'code_step': True}
                    await tg_client.send_message(
                        int(tg_id),
                        "📱 *Код подтверждения*\n\nВведите код из SMS:",
                        parse_mode='markdown'
                    )
                elif "starting 2fa password authentication" in line.lower():
                    pending_auth[tg_id] = {'password_step': True}
                    await tg_client.send_message(
                        int(tg_id),
                        "🔐 *2FA пароль*\n\nВведите пароль (или 0, если нет):",
                        parse_mode='markdown'
                    )
                elif "✅ MAX бот успешно запущен" in line:
                    if tg_id in pending_auth:
                        del pending_auth[tg_id]
                    await tg_client.send_message(
                        int(tg_id),
                        "✅ *MAX бот успешно запущен!*",
                        parse_mode='markdown'
                    )
    except Exception as e:
        print(f"❌ Ошибка чтения PTY: {e}")
    finally:
        if tg_id in processes:
            info = processes[tg_id]
            if 'transport' in info:
                info['transport'].close()
            if 'master_fd' in info:
                try:
                    os.close(info['master_fd'])
                except OSError:
                    pass
            del processes[tg_id]
        if tg_id in stdin_writer:
            del stdin_writer[tg_id]

async def send_to_worker_stdin(tg_id: str, text: str):
    writer = stdin_writer.get(tg_id)
    if writer and not writer.closed:
        writer.write((text + '\n').encode())
        writer.flush()
        return True
    return False

# --------------------- Команды Telegram ---------------------
@tg_client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.reply(
        "🤖 *MAX Reader Bot*\n"
        "/register – регистрация\n"
        "/start_bot – запуск\n"
        "/stop – остановка\n"
        "/status – статус\n"
        "/unregister – удалить аккаунт\n"
        "/cancel – отменить",
        parse_mode='markdown'
    )

@tg_client.on(events.NewMessage(pattern='/register'))
async def register_command(event):
    tg_id = str(event.sender_id)
    if tg_id in users:
        await event.reply("⚠️ Вы уже зарегистрированы. Используйте /unregister")
        return
    pending_auth[tg_id] = {'awaiting_phone': True}
    await event.reply("📱 Введите номер телефона в формате +71234567890")

@tg_client.on(events.NewMessage(pattern='/unregister'))
async def unregister_command(event):
    tg_id = str(event.sender_id)
    if tg_id in users:
        if tg_id in processes:
            processes[tg_id]['proc'].terminate()
        del users[tg_id]
        save_users()
        shutil.rmtree(os.path.join(CACHE_DIR, f"user_{tg_id}"), ignore_errors=True)
        await event.reply("✅ Удалён")
    else:
        await event.reply("❌ Не зарегистрирован")

@tg_client.on(events.NewMessage(pattern='/status'))
async def status_command(event):
    tg_id = str(event.sender_id)
    if tg_id not in users:
        await event.reply("❌ Не зарегистрирован")
        return
    running = tg_id in processes and processes[tg_id]['proc'].returncode is None
    status = "🟢 Активен" if running else "🔴 Остановлен"
    await event.reply(f"📊 Статус: {status}\n📱 {users[tg_id]['phone']}")

@tg_client.on(events.NewMessage(pattern='/stop'))
async def stop_command(event):
    tg_id = str(event.sender_id)
    if tg_id in processes:
        processes[tg_id]['proc'].terminate()
        await event.reply("🛑 Остановлен")
    else:
        await event.reply("❌ Не запущен")

@tg_client.on(events.NewMessage(pattern='/start_bot'))
async def start_bot_command(event):
    tg_id = str(event.sender_id)
    if tg_id not in users:
        await event.reply("❌ Сначала /register")
        return
    if tg_id in processes and processes[tg_id]['proc'].returncode is None:
        await event.reply("⚠️ Уже запущен")
        return
    phone = users[tg_id]['phone']
    if await start_max_worker(tg_id, phone):
        await event.reply("🚀 Запускаю...")
    else:
        await event.reply("❌ Ошибка запуска")

@tg_client.on(events.NewMessage(pattern='/cancel'))
async def cancel_command(event):
    tg_id = str(event.sender_id)
    if tg_id in pending_auth:
        del pending_auth[tg_id]
    await event.reply("❌ Отменено")

# Обработка ответов пользователя
@tg_client.on(events.NewMessage)
async def handle_text(event):
    if not event.is_private or event.text.startswith('/'):
        return
    tg_id = str(event.sender_id)
    text = event.text.strip()
    #print(text)

    if tg_id not in pending_auth:
        return

    if pending_auth[tg_id].get('awaiting_phone'):
        if not text.startswith('+'):
            await event.reply("❌ Неверный формат. Пример: +71234567890")
            return
        users[tg_id] = {
            'phone': text,
            'tg_id': tg_id,
            'active': True,
            'registered_at': datetime.now().isoformat()
        }
        save_users()
        await event.reply(f"✅ Номер сохранён: {text}\n🚀 Запускаю...")
        await start_max_worker(tg_id, text)
        del pending_auth[tg_id]
        return

    if pending_auth[tg_id].get('code_step'):
        if not text.isdigit():
            await event.reply("❌ Код должен содержать только цифры")
            return
        code_file = os.path.join(CACHE_DIR, f"user_{tg_id}", "code.txt")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(text)
        await event.reply("✅ Код отправлен")
        del pending_auth[tg_id]
        return

    if pending_auth[tg_id].get('password_step'):
        value = "" if text == "0" else text
        pwd_file = os.path.join(CACHE_DIR, f"user_{tg_id}", "password.txt")
        with open(pwd_file, "w", encoding="utf-8") as f:
            f.write(value)
        print(value)
        await event.reply("✅ Пароль отправлен")
        del pending_auth[tg_id]
        return

# HTTP обработчик
async def handle_send_message(request):
    try:
        data = await request.json()
        await tg_client.send_message(
            data['receiver_id'],
            f"📩 *{data.get('sender_name', 'Неизвестный')}*\n\n{data.get('text', '')}",
            parse_mode='markdown'
        )
        return web.json_response({"status": "ok"})
    except Exception as e:
        print(f"❌ HTTP ошибка: {e}")
        return web.json_response({"status": "error"}, status=500)

app = web.Application()
app.router.add_post('/send_to_tg', handle_send_message)
app.router.add_get('/health', lambda r: web.json_response({"status": "ok"}))

async def main():
    print("=" * 60)
    print("🚀 ЗАПУСК MAX READER BOT (PTY версия)")
    print("=" * 60)
    load_users()
    await tg_client.start(bot_token=TG_BOT_TOKEN)
    me = await tg_client.get_me()
    print(f"✅ Бот @{me.username} запущен")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', HTTP_PORT)
    await site.start()
    print(f"✅ HTTP сервер на порту {HTTP_PORT}")
    for tg_id, data in users.items():
        if data.get('phone'):
            print(f"🔄 Автозапуск для {tg_id}")
            await start_max_worker(tg_id, data['phone'])
    print("\n✅ БОТ ГОТОВ\n")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановлен")
        for info in processes.values():
            if info['proc'].returncode is None:
                info['proc'].terminate()