import telegram
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import google.generativeai as genai
import logging
import os
import asyncio
import io
import nest_asyncio
from telegram.helpers import escape_markdown

# Aktifkan jika error "event loop is already running" di Jupyter/VPS
nest_asyncio.apply()

# --- Konfigurasi ---
TELEGRAM_BOT_TOKEN = '7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA'
GEMINI_API_KEY = 'AIzaSyAgBNsxwQzFSVWQuEUKe7PkKykcX42BAx8'

# --- Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Inisialisasi Gemini AI ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    logger.info("Berhasil terhubung ke model Gemini.")
except Exception as e:
    logger.critical(f"Gagal mengkonfigurasi Gemini AI: {e}")
    exit()

# --- Prompt untuk analisis teknikal ---
ANALYSIS_PROMPT = """Anda adalah seorang analis teknikal pasar forex. Analisis screenshot chart trading berikut ini secara detail. Fokus pada elemen-elemen candle terakhir berikut jika terlihat dengan jelas di gambar:
1. Perkiraan Harga Saat Ini
2. Tren Utama
3. Pola Candlestick/Chart Signifikan
4. Kondisi Indikator Teknikal
5. Level Support dan Resistance
6. Gunakan strategi Fibonaci

Berdasarkan semua observasi di atas, berikan:
🔹 **Saran Trading Keseluruhan:** BUY, SELL, atau NETRAL
🔹 **Alasan Utama:** (minimal 2-3 poin)
🔹 **Level Penting (jika ada):**
  - 🟢 Entry point
  - 🎯 Target Profit
  - 🛑 Stop Loss

Gunakan format yang rapi dan jelas."""

# --- Fungsi utama analisis gambar ---
async def analyze_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Gambar diterima dari: {update.message.from_user.username}")
    processing_message = await update.message.reply_text("⏳ Menganalisis gambar dengan AI...")

    try:
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)

        with io.BytesIO() as image_buffer:
            await photo_file.download_to_memory(image_buffer)
            image_buffer.seek(0)

            contents = {
                'parts': [
                    {'mime_type': 'image/jpeg', 'data': image_buffer.getvalue()},
                    {'text': ANALYSIS_PROMPT}
                ]
            }

            logger.info("Mengirim gambar ke Gemini...")
            response = await model.generate_content_async(contents)
            logger.info("Respons diterima.")

        try:
            await processing_message.delete()
        except Exception as del_err:
            logger.warning(f"Gagal hapus pesan proses: {del_err}")

        escaped_response = escape_markdown(response.text, version=2)

        await update.message.reply_text(
            escaped_response,
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
        )
        logger.info("Respons dikirim ke user.")

    except Exception as e:
        logger.error(f"Kesalahan dalam analyze_image: {e}", exc_info=True)
        try:
            await processing_message.delete()
        except:
            pass
        await update.message.reply_text(
            "⚠️ Maaf, terjadi kesalahan saat menganalisis gambar. Silakan coba lagi nanti."
        )

# --- Main function ---
async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.PHOTO, analyze_image))

    logger.info("Bot siap! Menunggu gambar untuk dianalisis...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
