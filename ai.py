import telegram
from telegram.ext import Application, MessageHandler, ContextTypes
from telegram.ext import filters
import google.generativeai as genai
import logging
import os
import asyncio

TELEGRAM_BOT_TOKEN = '7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA'
GEMINI_API_KEY = 'AIzaSyAgBNsxwQzFSVWQuEUKe7PkKykcX42BAx8'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro-vision')

ANALYSIS_PROMPT = """Anda adalah seorang analis teknikal pasar forex. Analisis ini bersifat Profesional dan Tingkat kecerdasan Program.\n\nAnalisis screenshot chart trading berikut ini secara detail. Fokus pada elemen-elemen candle terakhir berikut jika terlihat dengan jelas di gambar:\n1. Perkiraan Harga Saat Ini: (jika ada skala harga yang jelas dan mudah dibaca).\n2. Tren Utama: (Contoh: Naik, Turun, Sideways/Konsolidasi).\n3. Pola Candlestick/Chart Signifikan: (Contoh: Doji di Puncak/Lembah, Engulfing, Hammer, Shooting Star, Head and Shoulders, Double Top/Bottom, Triangle, Flag, Wedge, Channel).\n4. Kondisi Indikator Teknikal Utama (jika terlihat jelas): (Contoh: RSI (Oversold <30, Overbought >70, Divergence), MACD (Golden/Death Cross, Divergence, Posisi Histogram), Moving Averages (Posisi harga terhadap MA, Golden/Death Cross MA), Bollinger Bands (Harga menyentuh upper/lower band, Squeeze)).\n5. Level Support dan Resistance Kunci: (Identifikasi beberapa level S&R penting yang terlihat).\n\n6. Gunakan strategi Pola 7 Candle & Teknik 7 Naga.\nBerdasarkan semua observasi di atas, berikan:\n🔹 **Saran Trading Keseluruhan:** (BUY, SELL, atau NETRAL/WAIT)\n🔹 **Alasan Utama (poin-poin):** (Berikan minimal 2-3 alasan utama untuk saran trading Anda, merujuk pada observasi dari poin 1-6 di atas).\n🔹 **Potensi Level Penting (jika teridentifikasi dari chart):**\n  - 🟢 Open Posisi potensial: [jika ada]\n  - 🎯 Target Profit (TP) potensial: [jika ada]\n  - 🛑 Stop Loss (SL) potensial: [jika ada]\n\nStruktur jawaban Anda sebaiknya jelas, terperinci, dan menggunakan tampilan yang keren atau point setiap bagian."""

async def analyze_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive('user_image.jpg')
    logger.info("Gambar diterima dari %s", user.first_name)

    processing_message = await update.message.reply_text("⏳ Sedang menganalisis gambar Anda... Mohon tunggu sebentar.")

    try:
        with open('user_image.jpg', 'rb') as image_file:
            image_data = image_file.read()

        contents = [
            {"mime_type": "image/jpeg", "data": image_data},
            {"text": ANALYSIS_PROMPT}
        ]

        response = await model.generate_content(contents)
        analysis_text = response.text.strip()
        analysis_lines = analysis_text.split('\n')

        formatted_response = "📈 **Analisis Trading Profesional** 📉\n\n"
        for line in analysis_lines:
            if line.startswith("1. Perkiraan Harga Saat Ini:"):
                formatted_response += f"💰 {line}\n"
            elif line.startswith("2. Tren Utama:"):
                formatted_response += f"📊 {line}\n"
            elif line.startswith("3. Pola Candlestick/Chart Signifikan:"):
                formatted_response += f"🕯️ {line}\n"
            elif line.startswith("4. Kondisi Indikator Teknikal Utama"):
                formatted_response += f"⚙️ {line}\n"
            elif line.startswith("5. Level Support dan Resistance Kunci"):
                formatted_response += f"🛡️ {line}\n"
            else:
                formatted_response += f"{line}\n"

        await processing_message.delete()
        await update.message.reply_text(formatted_response, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error("Error saat analisis gambar: %s", e)
        await update.message.reply_text("⚠️ Maaf, terjadi kesalahan saat menganalisis gambar Anda. Silakan coba lagi nanti.")
    finally:
        if os.path.exists('user_image.jpg'):
            os.remove('user_image.jpg')

async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    photo_handler = MessageHandler(filters.PHOTO, analyze_image)
    application.add_handler(photo_handler)

    logger.info("Bot Telegram sudah berjalan...")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio

    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
