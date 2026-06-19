# group_search.py
from telethon import TelegramClient
from config import API_ID, API_HASH, PHONE_NUMBER

client = TelegramClient('session', API_ID, API_HASH)

async def search_group_history(group_id, query, limit=100):
    """جستجو در تاریخچه یک گروه"""
    try:
        await client.start(phone=PHONE_NUMBER)
        entity = await client.get_entity(group_id)
        
        messages = await client.get_messages(entity, limit=limit)
        for msg in messages:
            if msg.text and query.lower() in msg.text.lower():
                return msg
        return None
    except Exception as e:
        print(f"Error searching group {group_id}: {e}")
        return None

async def search_all_groups(query, groups_list):
    """جستجو در لیستی از گروه‌ها"""
    for group in groups_list:
        result = await search_group_history(group, query)
        if result:
            return result
    return None
