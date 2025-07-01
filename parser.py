import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilterChatlist
from dotenv import load_dotenv
import os

load_dotenv()

api_hash = os.getenv("API_HASH")
api_id = int(os.getenv("API_ID"))
session_name = 'user_session'

client = TelegramClient(session_name, api_id, api_hash)

async def get_folders():
    result = await client(GetDialogFiltersRequest())
    folders = []
    for f in result.filters:
        if isinstance(f, DialogFilterChatlist):
            folders.append((f, f.title.text))
    return folders

async def get_chats_from_folder(folder):
    chat_ids = []
    for peer in folder.include_peers:
        try:
            entity = await client.get_entity(peer)
            chat_ids.append(entity)
        except Exception as e:
            print(f"⚠️ Не вдалося отримати чат з peer {peer}: {e}")
    return chat_ids

async def main():
    print("📂 Підключаємося до Telegram...")
    await client.start()

    print("📂 Отримуємо список папок Telegram...")
    folders = await get_folders()

    if not folders:
        print("❌ Немає доступних папок.")
        return

    print("\n🔖 Доступні папки:")
    for idx, folder in enumerate(folders, 1):
        print(f"{idx}: {folder[1]}")  # folder[1] — це назва папки

    selected_input = input("\nВведи номери папок для моніторингу (через пробіл): ").strip()
    if not selected_input:
        print("❌ Папка не обрана або введено некоректне значення.")
        return

    try:
        selected_indices = [int(i) - 1 for i in selected_input.split()]
    except:
        print("❌ Некоректні номери папок.")
        return

    selected_folders = []
    for i in selected_indices:
        if 0 <= i < len(folders):
            selected_folders.append(folders[i][0])  # folder[0] — це сам об'єкт фільтра

    if not selected_folders:
        print("❌ Жодна папка не вибрана.")
        return

    folder_keywords = {}
    monitored_chats = set()

    for folder in selected_folders:
        words = input(f"Введи ключові слова через пробіл для папки '{folder.title.text}': ").strip().lower()
        keywords = [w for w in words.split() if w]
        if not keywords:
            print(f"❌ Для папки '{folder.title.text}' не введено ключових слів, вона пропускається.")
            continue

        chats = await get_chats_from_folder(folder)
        if not chats:
            print(f"⚠️ У папці '{folder.title.text}' немає чатів.")
            continue

        folder_keywords[folder.title.text] = {
            'keywords': keywords,
            'chats': chats
        }
        monitored_chats.update(chat.id for chat in chats)

    if not folder_keywords:
        print("❌ Немає папок з ключовими словами і чатами для моніторингу.")
        return

    target_user = input("Введи username або ID користувача, кому надсилати повідомлення: ").strip()
    print("\n🚀 Запускаємо моніторинг повідомлень... Ctrl+C для виходу.\n")

    @client.on(events.NewMessage(chats=list(monitored_chats)))
    async def handler(event):
        message_text = event.raw_text.lower()
        chat = event.chat

        for folder_title, data in folder_keywords.items():
            if chat in data['chats']:
                if any(keyword in message_text for keyword in data['keywords']):
                    try:
                        await client.forward_messages(target_user, event.message)
                        print(f"Переслано повідомлення з чату '{chat.title or chat.username}' у папці '{folder_title}' користувачу {target_user}")
                    except Exception as e:
                        print(f"Помилка при пересиланні повідомлення: {e}")
                    break

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
