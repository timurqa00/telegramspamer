from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilter, DialogFilterChatlist
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import os

load_dotenv()
api_hash = os.getenv("API_HASH")
api_id = int(os.getenv("API_ID"))
session_name = 'user_session'

client = TelegramClient(session_name, api_id, api_hash)
client.start()


def get_chat_folders():
    result = client(GetDialogFiltersRequest())
    # Повертаємо список (фільтр, назва папки)
    folders = []
    for f in result.filters:
        # Для звичайних фільтрів з назвою (DialogFilterChatlist)
        if isinstance(f, DialogFilterChatlist):
            folders.append((f, f.title.text))
    return folders


def get_chats_from_folder(folder):
    chat_ids = []
    for peer in folder.include_peers:
        try:
            entity = client.get_entity(peer)
            chat_ids.append(entity.id)
        except Exception as e:
            print(f"⚠️ Не вдалося отримати чат з peer {peer}: {e}")
    return chat_ids


def prompt_folder_selection(folders):
    print("\n🔖 Доступні папки:")
    for idx, (_, title) in enumerate(folders, 1):
        print(f"{idx}: {title}")

    selected = input("\nВведи номери папок для розсилки (через пробіл): ").strip().split()
    indices = []
    for s in selected:
        try:
            idx = int(s) - 1
            if 0 <= idx < len(folders):
                indices.append(idx)
        except:
            continue
    return [folders[i] for i in indices]


def get_message_for_folder(folder_title):
    print(f"\n✉️ Введи текст повідомлення для папки '{folder_title}':")
    return input("> ").strip()


def get_cooldown_for_folder(folder_title):
    while True:
        try:
            cooldown = int(input(f"⏱ Введи cooldown (в хвилинах) для '{folder_title}': ").strip())
            return cooldown
        except:
            print("❌ Невірне значення, спробуй ще раз.")


def start_global_loop_multiple(folder_tasks):
    last_sent_times = {}  # chat_id -> datetime
    print("\n🚀 Починаємо розсилку... натисни Ctrl+C щоб зупинити")

    while True:
        now = datetime.now()

        for folder_title, chats, message, cooldown in folder_tasks:
            for chat_id in chats:
                last_time = last_sent_times.get(chat_id)
                cooldown_passed = not last_time or now - last_time >= timedelta(minutes=cooldown)

                if cooldown_passed:
                    try:
                        client.send_message(chat_id, message)
                        last_sent_times[chat_id] = now
                        print(f"[{now.strftime('%H:%M:%S')}] ✅ Повідомлення надіслано до {chat_id} ({folder_title})")
                    except Exception as e:
                        print(f"[{now.strftime('%H:%M:%S')}] ⚠️ Помилка в {chat_id}: {e}")
                else:
                    remaining = (timedelta(minutes=cooldown) - (now - last_time)).seconds // 60
                    print(f"[{now.strftime('%H:%M:%S')}] ⏳ Чат {chat_id} ({folder_title}) в cooldown ({remaining} хв залишилось)")

        print("\n🕐 Чекаємо 1 хвилину перед наступною спробою...\n")
        time.sleep(60)


def main():
    print("📂 Отримуємо список папок Telegram...")
    folders = get_chat_folders()

    if not folders:
        print("❌ Немає доступних папок.")
        return

    selected_folders = prompt_folder_selection(folders)
    if not selected_folders:
        print("❌ Жодна папка не обрана або введено некоректне значення.")
        return

    folder_tasks = []

    for folder, folder_title in selected_folders:
        chats = get_chats_from_folder(folder)
        if not chats:
            print(f"⚠️ У папці '{folder_title}' немає чатів.")
            continue

        message = get_message_for_folder(folder_title)
        cooldown = get_cooldown_for_folder(folder_title)
        folder_tasks.append((folder_title, chats, message, cooldown))

    if not folder_tasks:
        print("❌ Немає активних чатів для розсилки.")
        return

    start_global_loop_multiple(folder_tasks)


if __name__ == '__main__':
    main()
