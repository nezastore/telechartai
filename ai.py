import telegram
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import google.generativeai as genai
import logging
import os
import asyncio
import io
import nest_asyncio  # OPSIONAL: Aktifkan jika Anda menjalankan di Jupyter/lingkungan interaktif

# OPSIONAL: Hilangkan tanda pagar di baris bawah jika Anda mendapat error "event loop is already running"
nest_asyncio.apply()

# --- Konfigurasi (TIDAK DIUBAH) ---
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
    logger.info("Berhasil terhubung ke model Gemini: gemini-1.5-flash-latest")
except Exception as e:
    logger.critical(f"Gagal mengkonfigurasi Gemini AI. Periksa API Key Anda. Error: {e}")
    exit()

# --- Prompt Analisis (TIDAK DIUBAH) ---
ANALYSIS_PROMPT = """Anda adalah seorang analis teknikal pasar forex. Analisis screenshot chart trading berikut ini secara detail. Fokus pada elemen-elemen candle terakhir berikut jika terlihat dengan jelas di gambar:\n1. Perkiraan Harga Saat Ini: (jika ada skala harga yang jelas dan mudah dibaca).\n2. Tren Utama: (Contoh: Naik, Turun, Sideways/Konsolidasi).\n3. Pola Candlestick/Chart Signifikan: (Contoh: Doji di Puncak/Lembah, Engulfing, Hammer, Shooting Star, Head and Shoulders, Double Top/Bottom, Triangle, Flag, Wedge, Channel).\n4. Kondisi Indikator Teknikal Utama (jika terlihat jelas): (Contoh: RSI (Oversold <30, Overbought >70, Divergence), MACD (Golden/Death Cross, Divergence, Posisi Histogram), Moving Averages (Posisi harga terhadap MA, Golden/Death Cross MA), Bollinger Bands (Harga menyentuh upper/lower band, Squeeze)).\n5. Level Support dan Resistance Kunci: (Identifikasi beberapa level S&R penting yang terlihat).\n\n6. Gunakan strategi Pola 7 Candle & Teknik 7 Naga.\nBerdasarkan semua observasi di atas, berikan:\n🔹 **Saran Trading Keseluruhan:** (BUY, SELL, atau NETRAL/WAIT)\n🔹 **Alasan Utama (poin-poin):** (Berikan minimal 2-3 alasan utama untuk saran trading Anda, merujuk pada observasi dari poin 1-6 di atas).\n🔹 **Potensi Level Penting (jika teridentifikasi dari chart):**\n  - 🟢 Open Posisi potensial: [jika ada]\n  - 🎯 Target Profit (TP) potensial: [jika ada]\n  - 🛑 Stop Loss (SL) potensial: [jika ada]\n\nStruktur jawaban Anda sebaiknya jelas, terperinci, dan menggunakan tampilan yang keren atau point setiap bagian."""

async def analyze_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Menganalisis gambar yang dikirim pengguna menggunakan AI."""
    logger.info(f"Gambar diterima dari pengguna: {update.message.from_user.username}")
    
    processing_message = await update.message.reply_text("⏳ Menganalisis gambar dengan Ai...")

    try:
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)

        # Gunakan buffer dan auto-hapus setelah keluar blok
        with io.BytesIO() as image_buffer:
            await photo_file.download_to_memory(image_buffer)
            image_buffer.seek(0)

            contents = {
                'parts': [
                    {'mime_type': 'image/jpeg', 'data': image_buffer.getvalue()},
                    {'text': ANALYSIS_PROMPT}
                ]
            }

            logger.info("Memanggil model Gemini AI...")
            response = await model.generate_content_async(contents)
            logger.info("Respons dari Gemini AI berhasil diterima.")

        await processing_message.delete()

        await update.message.reply_text(
            response.text,
            parse_mode=telegram.constants.ParseMode.MARKDOWN
        )
        logger.info("Respons berhasil dikirim ke Telegram.")

    except Exception as e:
        logger.error(f"Terjadi kesalahan dalam analyze_image: {e}", exc_info=True)
        await processing_message.delete()
        await update.message.reply_text(
            "⚠️ Maaf, terjadi kesalahan saat menganalisis gambar Anda. "
            "Pastikan gambar jelas atau coba lagi nanti."
        )

async def main():
    """Fungsi utama untuk menjalankan bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.PHOTO, analyze_image))

    logger.info("Bot Telegram siap dijalankan... Menunggu gambar untuk dianalisis.")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
