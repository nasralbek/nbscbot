import os
import requests
import yt_dlp
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from mutagen.mp3 import MP3
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from io import BytesIO



# Функция для скачивания трека и обложки
def download_track(url):
    ydl_opts = {
        'format':
        'bestaudio[ext=mp3]/bestaudio',  # Скачиваем аудиофайл в формате MP3
        'outtmpl':
        'downloads/%(title)s.%(ext)s',  # Сохраняем трек в папку 'downloads'
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        return file_path, info_dict


# Функция для изменения тегов MP3
def set_mp3_tags(file_path, title, artist, thumbnail_url):
    audio = MP3(file_path, ID3=ID3)

    # Устанавливаем теги
    audio.tags = ID3()  # Создаем новый объект ID3
    audio.tags.add(TIT2(encoding=3, text=title))  # Название трека
    audio.tags.add(TPE1(encoding=3, text=artist))  # Исполнитель
    if thumbnail_url:
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            audio.tags.add(APIC(
                encoding=3,  # UTF-8
                mime='image/jpeg',  # MIME-тип изображения
                type=3,  # Обложка
                desc='Cover',
                data=img_data.read()
            ))
    audio.save()  # Сохраняем изменения


# Функция для обработки команды /start
async def start(update: Update, context):
    await update.message.reply_text(
        "Пришлите ссылку на трек из SoundCloud, чтобы скачать его.")


# Функция для обработки сообщений с ссылкой
async def handle_message(update: Update, context) -> None:
    url = update.message.text
    await context.bot.delete_message(chat_id=update.effective_chat.id,message_id=update.message.id)

    if 'soundcloud.com' in url:
        #await update.message.reply_text("Sending...")
        try:
            file_path, info_dict = download_track(url)  # Скачиваем трек
            title = info_dict.get('title', 'Unknown Title')
            artist = info_dict.get('uploader', 'Unknown Artist')
            thumbnail_url = info_dict.get('thumbnail', None)

            # Устанавливаем теги MP3
            set_mp3_tags(file_path, title, artist, thumbnail_url)

            # Отправляем аудиофайл пользователю с кликабельными ссылками
            with open(file_path, 'rb') as audio_file:
                caption = (
                    f"\\[ [Link]({url}) ] | "  # Сделаем ссылку на трек кликабельной
                    f"\\[ [Cover]({thumbnail_url}) ]"  # Сделаем ссылку на обложку кликабельной
                )
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    caption=caption,
                    parse_mode=
                    'Markdown',  # Указываем, что мы используем Markdown
                )

                # Удаляем временный файл
                os.remove(file_path)

        except Exception as e:
            await update.message.reply_text(f"Произошла ошибка: {e}")
    else:
        await update.message.reply_text("Send SoundCloud link")


# Основной блок для запуска бота
def main():
    # Вставьте сюда токен вашего бота
    TOKEN = '7575941939:AAHP2zS9MwreSW8H0CdDpbZfjPpfFrBvOJU'

    # Создание приложения бота
    application = Application.builder().token(TOKEN).build()

    # Добавление обработчика сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    # Создаем папку для загрузки файлов, если ее нет
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    main()
