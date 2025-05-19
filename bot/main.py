import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv
from db import add_word, get_due_words, update_word_interval, get_word_info, word_exists, delete_word
from utils import translate_word, get_next_reminder_time

dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer('Привет! Отправь мне английское слово или фразу, и я помогу тебе их запомнить.')


@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Проверяем, заканчивается ли текст на ~
    if text.endswith('~'):
        # Убираем ~ и разбиваем на слова
        text = text[:-1].strip()
        # Убираем знаки препинания и разбиваем на слова
        words = [word.strip('.,!?;:()[]{}"\'') for word in text.split()]
        translations = []
        skipped_words = []
        
        for word in words:
            if word_exists(user_id, word):
                skipped_words.append(word)
                continue
                
            ru = translate_word(word)
            if add_word(user_id, word, ru):
                translations.append(f'{word} — {ru}')
        
        response = []
        if translations:
            response.append('\n'.join(translations))
            response.append('Я запомнил эти новые слова для тебя!')
        if skipped_words:
            response.append(f'Слова {", ".join(skipped_words)} уже есть в твоем словаре.')
            
        await message.answer('\n'.join(response))
    else:
        # Проверяем существование фразы
        if word_exists(user_id, text):
            await message.answer(f'Фраза "{text}" уже есть в твоем словаре.')
            return
            
        # Обрабатываем как единую фразу
        ru = translate_word(text)
        if add_word(user_id, text, ru):
            await message.answer(f'{text} — {ru}\nЯ запомнил эту фразу для тебя!')

# Клавиатура для повторения
def get_reminder_keyboard(word):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Хорошо помню", callback_data=f"rem_good|{word}"),
            InlineKeyboardButton(text="Помню с трудом", callback_data=f"rem_hard|{word}"),
            InlineKeyboardButton(text="Не помню", callback_data=f"rem_bad|{word}")
        ],
        [
            InlineKeyboardButton(text="Показать перевод", callback_data=f"show|{word}"),
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete|{word}")
        ]
    ])

@dp.callback_query(lambda c: c.data.startswith("show|"))
async def show_translation(callback: CallbackQuery):
    word = callback.data.split("|", 1)[1]
    user_id = callback.from_user.id
    info = get_word_info(user_id, word)
    if info:
        await callback.message.edit_text(
            f"{word} — {info['ru']}",
            reply_markup=get_reminder_keyboard(word)
        )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("rem_"))
async def handle_reminder_feedback(callback: CallbackQuery):
    action, word = callback.data.split("|", 1)
    user_id = callback.from_user.id
    # Получаем текущий интервал
    info = get_word_info(user_id, word)
    interval = info['interval']
    if action == "rem_good":
        new_interval = interval * 3
    elif action == "rem_hard":
        new_interval = int(interval * 1.5)
    else:  # rem_bad
        new_interval = interval
    update_word_interval(user_id, word, new_interval)
    
    # Удаляем сообщение с карточкой
    await callback.message.delete()
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("delete|"))
async def delete_word_handler(callback: CallbackQuery):
    word = callback.data.split("|", 1)[1]
    user_id = callback.from_user.id
    
    # Удаляем слово из базы
    delete_word(user_id, word)
    
    # Удаляем сообщение с карточкой
    await callback.message.delete()
    
    # Отправляем подтверждение удаления
    msg = await callback.message.answer(f'Слово "{word}" удалено из твоего словаря.')
    await asyncio.sleep(3)
    await msg.delete()
    
    await callback.answer()

async def reminder_loop():
    while True:
        due = get_due_words()
        for user_id, word, ru in due:
            try:
                await bot.send_message(
                    user_id,
                    f"Вспомни перевод: {word}",
                    reply_markup=get_reminder_keyboard(word)
                )
            except Exception as e:
                logging.error(f'Ошибка отправки напоминания: {e}')
        await asyncio.sleep(60)

async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError('TELEGRAM_TOKEN не найден в .env')
    global bot
    bot = Bot(token=token)
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
