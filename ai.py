import telegram
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import google.generativeai as genai
import logging
import os
import asyncio
import io
import nest_asyncio
import re

# Aktifkan jika error "event loop is already running"
nest_asyncio.apply()

# --- Konfigurasi ---
TELEGRAM_BOT_TOKEN = '7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA'
GEMINI_API_KEY = 'AIzaSyAgBNsxwQzFSVWQuEUKe7PkKykcX42BAx8'

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Inisialisasi Gemini ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    logger.info("Berhasil terhubung ke Gemini AI.")
except Exception as e:
    logger.critical(f"Gagal koneksi ke Gemini: {e}")
    exit()

# Prompt analisa
ANALYSIS_PROMPT = """Anda adalah analis teknikal trading forex profesional . Tolong analisis chart trading dari gambar berikut,Dan mohon berikan arahan mau kemana arah candle berikutnya,Saya ingin strategi  forex Dengan presentase 90% yang mampu memberikan keuntungan konsisten dalam waktu singkat. Tolong jelaskan metode yang paling efektif dengan kombinasi AI, Sertakan juga contoh setup trading berdasarkan arah candle terakhir yanag ada di screnshoot. Saya ingin strategi yang cocok untuk kondisi pasar, serta cara menghindari sinyal palsu agar trading saya lebih akurat dan disiplin.:
1. Harga saat ini (jika terlihat)
2. Arah tren Market
3. Pola candlestick/chart penting 
4. Indikator teknikal yang terlihat (misalnya moving average, RSI, Bollinger Bands, dll) dan sinyal yang dihasilkan
5. Level support/resistance penting
6. Gunakan strategi scalping yang efektif

Berikan saran trading berdasarkan observasi di atas:
- Saran: Buy / Sell / Netral
- Alasan utama (minimal 2-3)
- Level penting: Entry, TP, SL
- Pola candlestick atau price action yang menonjol

Jawaban harus jelas, singkat, mudah dipahami."""


# Fungsi untuk menghapus tanda ** dan merapikan
def clean_text(text):
    # Hapus semua tanda **
    text = re.sub(r"\*\*", "", text)
    # Optional: bisa hapus tanda * tunggal juga jika mau lebih bersih
    text = re.sub(r"\*", "", text)
    return text.strip()


# Fungsi analisis
async def analyze_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Gambar dari: {update.message.from_user.username}")
    loading = await update.message.reply_text("⏳ Gambar diterima, menganalisis dengan AI...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        with io.BytesIO() as buffer:
            await file.download_to_memory(buffer)
            buffer.seek(0)

            contents = {
                'parts': [
                    {'mime_type': 'image/jpeg', 'data': buffer.getvalue()},
                    {'text': ANALYSIS_PROMPT}
                ]
            }

            logger.info("Memproses di Gemini...")
            result = await model.generate_content_async(contents)
            logger.info("Jawaban diterima dari Gemini")

        try:
            await loading.delete()
        except:
            pass

        clean_response = clean_text(result.text)
        await update.message.reply_text(clean_response)

    except Exception as e:
        logger.error(f"Error saat analisis: {e}")
        try:
            await loading.delete()
        except:
            pass
        await update.message.reply_text("❗ Terjadi kesalahan saat memproses gambar. Coba lagi nanti.")

# Fungsi utama
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, analyze_image))
    logger.info("Bot aktif. Menunggu gambar...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
