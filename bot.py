import asyncio, logging, sys, aiogram, os, string, random
import speech_recognition as sr
from pydub import AudioSegment
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import aiohttp

#Токен бот из https://t.me/BotFather
TOKEN = 'TOKEN'

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class CV:
    """Общий класс для конвертации"""
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def generate_name(len):
        """Генерация имени"""
        return ''.join(random.choice([i for i in (string.ascii_letters + '1234567890')]) for i in range(len))

    @staticmethod
    async def download_voice(voice):
        """Скачивания аудио"""
        file_id = voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        filename = CV.generate_name(8)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.telegram.org/file/bot{TOKEN}/{file_path}') as response:
                if response.status == 200:
                    with open(f'utils/audio/{filename}.mp3', 'wb') as f:
                        f.write(await response.read())

        return filename

    @staticmethod
    async def audio_to_text(message: Message, voice):
        """Конвертация в текст"""
        recognizer = sr.Recognizer()
        filename = await CV.download_voice(voice)

        audio = AudioSegment.from_file(f'utils/audio/{filename}.mp3')
        audio.export(f"utils/audio/{filename}.wav", format="wav")
        with sr.AudioFile(f"utils/audio/{filename}.wav") as source:
            await message.edit_text(text='Конвертирую в текст.')
            audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                return text, 's'
            except sr.UnknownValueError:
                return None, 'f'
            except sr.RequestError as e:
                return e, 'e'

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await message.answer(text='Чтобы расшифровать аудио, тебе нужно переслать голосовое сообщение или файл в этот чат.\n\nБот был создан @roozzz1m\nTelegram канал - https://t.me/roozzz1m_tt')

@dp.message()
async def voice_message(message: Message):
    if(message.voice or message.audio):
        msg = await message.answer(text='Получаю аудио.')
        
        if message.voice:
            output = await CV.audio_to_text(msg, message.voice)
        else:
            output = await CV.audio_to_text(msg, message.audio)

        if output[1] == 's':
            await msg.reply(text=output[0])

        elif output[1] == 'f':
            await msg.edit_text(text='Не удалось распознать текст.')

        elif output[1] == 'e':
            await msg.edit_text(text=f'Ошибка сервера: {output[1]}')

    else:
        await message.answer(text='Вы отправили сообщение в неправильном формате. Бот принимает только аудиофайлы в формате mp3 или голосовые сообщения.')

def delete_all_files_in_folder(folder_path):
    """При включении бота все аудиофайлы будут удаляться, чтобы избежать засорения директории."""
    if not os.path.exists(folder_path):
        return
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Не удалось удалить файл '{file_path}'. Причина: {e}")

async def main(bot, dp) -> None:
    """Запуск бота"""
    delete_all_files_in_folder('utils/audio/')

    await bot(aiogram.methods.DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main(bot=bot, dp=dp))
    
