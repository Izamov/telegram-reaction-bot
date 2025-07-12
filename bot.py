import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from collections import defaultdict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.getenv("API_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

reaction_counts = defaultdict(lambda: {"🌚": 0, "🍓": 0, "❤️‍🔥": 0})
user_reacted = defaultdict(set)

def create_reaction_keyboard(message_id):
    counts = reaction_counts[message_id]
    keyboard = InlineKeyboardMarkup(row_width=3)
    for emoji in ["🌚", "🍓", "❤️‍🔥"]:
        count = counts.get(emoji, 0)
        button = InlineKeyboardButton(text=f"{emoji} {count}", callback_data=f"react|{message_id}|{emoji}")
        keyboard.insert(button)
    return keyboard

@dp.message_handler(content_types=types.ContentType.ANY)
async def publish_to_channel(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    sent_msg = None
    if message.content_type == types.ContentType.PHOTO:
        sent_msg = await bot.send_photo(CHANNEL_ID, photo=message.photo[-1].file_id, caption=message.caption or "", reply_markup=create_reaction_keyboard(message.message_id))
    elif message.content_type == types.ContentType.VIDEO:
        sent_msg = await bot.send_video(CHANNEL_ID, video=message.video.file_id, caption=message.caption or "", reply_markup=create_reaction_keyboard(message.message_id))
    elif message.content_type == types.ContentType.STICKER:
        sent_msg = await bot.send_sticker(CHANNEL_ID, sticker=message.sticker.file_id, reply_markup=create_reaction_keyboard(message.message_id))
    elif message.text:
        sent_msg = await bot.send_message(CHANNEL_ID, text=message.text, reply_markup=create_reaction_keyboard(message.message_id))

    if sent_msg:
        reaction_counts[sent_msg.message_id] = {"🌚": 0, "🍓": 0, "❤️‍🔥": 0}
        user_reacted[sent_msg.message_id] = set()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("react|"))
async def handle_reaction(callback_query: types.CallbackQuery):
    _, message_id, emoji = callback_query.data.split("|")
    message_id = int(message_id)
    user_id = callback_query.from_user.id

    if user_id in user_reacted[message_id]:
        await callback_query.answer("Вы уже голосовали", show_alert=True)
        return

    reaction_counts[message_id][emoji] += 1
    user_reacted[message_id].add(user_id)

    try:
        await bot.edit_message_reply_markup(chat_id=CHANNEL_ID, message_id=message_id, reply_markup=create_reaction_keyboard(message_id))
    except:
        pass

    try:
        await bot.send_message(OWNER_ID, f"👤 {callback_query.from_user.full_name} нажал {emoji} на пост #{message_id}")
    except:
        pass

    await callback_query.answer()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)