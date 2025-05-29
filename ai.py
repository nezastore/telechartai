import telegram
from telegram.ext import Application, MessageHandler, ContextTypes
from telegram.ext import filters
import google.generativeai as genai
import logging
import os
import asyncio
import nest_asyncio # Mengimpor nest_asyncio

nest_asyncio.apply() # Menerapkan patch nest_asyncio untuk mengatasi masalah event loop

# Ganti dengan token bot Telegram Anda
TELEGRAM_BOT_TOKEN = '7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA'
# Ganti dengan API key Gemini Anda
GEMINI_API_KEY = 'AIzaSyAgBNsxwQzFSVWQuEUKe7PkKykcX42BAx8'

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
# Menggunakan model yang didukung untuk visi
model = genai.GenerativeModel('gemini-1.0-pro-vision-latest')

# Prompt analisis yang akan dikirimkan ke Gemini AI bersama dengan gambar
ANALYSIS_PROMPT = """Anda adalah seorang analis teknikal pasar forex. Analisis screenshot chart trading berikut ini secara detail. Fokus pada elemen-elemen candle terakhir berikut jika terlihat dengan jelas di gambar:\n1. Perkiraan Harga Saat Ini: (jika ada skala harga yang jelas dan mudah dibaca).\n2. Tren Utama: (Contoh: Naik, Turun, Sideways/Konsolidasi).\n3. Pola Candlestick/Chart Signifikan: (Contoh: Doji di Puncak/Lembah, Engulfing, Hammer, Shooting Star, Head and Shoulders, Double Top/Bottom, Triangle, Flag, Wedge, Channel).\n4. Kondisi Indikator Teknikal Utama (jika terlihat jelas): (Contoh: RSI (Oversold <30, Overbought >70, Divergence), MACD (Golden/Death Cross, Divergence, Posisi Histogram), Moving Averages (Posisi harga terhadap MA, Golden/Death Cross MA), Bollinger Bands (Harga menyentuh upper/lower band, Squeeze)).\n5. Level Support dan Resistance Kunci: (Identifikasi beberapa level S&R penting yang terlihat).\n\n6. Gunakan strategi Pola 7 Candle & Teknik 7 Naga.\nBerdasarkan semua observasi di atas, berikan:\n🔹 **Saran Trading Keseluruhan:** (BUY, SELL, atau NETRAL/WAIT)\n🔹 **Alasan Utama (poin-poin):** (Berikan minimal 2-3 alasan utama untuk saran trading Anda, merujuk pada observasi dari poin 1-6 di atas).\n🔹 **Potensi Level Penting (jika teridentifikasi dari chart):**\n  - 🟢 Open Posisi potensial: [jika ada]\n  - 🎯 Target Profit (TP) potensial: [jika ada]\n  - 🛑 Stop Loss (SL) potensial: [jika ada]\n\nStruktur jawaban Anda sebaiknya jelas, terperinci, dan menggunakan tampilan yang keren atau point setiap bagian."""

async def analyze_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menganalisis gambar yang dikirimkan pengguna menggunakan Gemini AI dengan logging detail.
    """
    logger.info("analyze_image dipanggil")
    user = update.message.from_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive('user_image.jpg')
    logger.info(f"Gambar diterima dan disimpan dari {user.first_name}")

    processing_message = await update.message.reply_text("⏳ Sedang menganalisis gambar Anda... Mohon tunggu sebentar.")

    try:
        with open('user_image.jpg', 'rb') as image_file:
            image_data = image_file.read()

        contents = [
            {"mime_type": "image/jpeg", "data": image_data},
            {"text": ANALYSIS_PROMPT}
        ]

        logger.info("Memanggil model Gemini AI...")
        response = await model.generate_content(contents)
        logger.info("Respons dari model Gemini AI diterima.")
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
            elif line.startswith("5. Level Support dan Resistance Kunci:"):
                formatted_response += f"🧱 {line}\n"
            elif line.startswith("6. Gunakan strategi"):
                formatted_response += f"🐉 {line}\n"
            elif line.startswith("🔹 **Saran Trading Keseluruhan:**"):
                formatted_response += f"\n✅ **{line.replace('🔹 **', '').replace(':**', '')}**\n"
            elif line.startswith("🔹 **Alasan Utama (poin-poin):**"):
                formatted_response += f"📌 **{line.replace('🔹 **', '').replace(':**', '')}**\n"
            elif line.startswith("🔹 **Potensi Level Penting (jika teridentifikasi dari chart):**"):
                formatted_response += f"\n🔑 **{line.replace('🔹 **', '').replace(':**', '')}**\n"
            elif line.startswith("  - 🟢 Open Posisi potensial:"):
                formatted_response += f"   🟢 {line.replace('  - 🟢 ', '')}\n"
            elif line.startswith("  - 🎯 Target Profit (TP) potensial:"):
                formatted_response += f"   🎯 {line.replace('  - 🎯 ', '')}\n"
            elif line.startswith("  - 🛑 Stop Loss (SL) potensial:"):
                formatted_response += f"   🛑 {line.replace('  - 🛑 ', '')}\n"
            else:
                formatted_response += f"{line}\n"

        logger.info(f"Respons yang diformat: {formatted_response}")
        await processing_message.delete()
        await update.message.reply_text(formatted_response, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        logger.info("Respons berhasil dikirim ke Telegram.")

    except Exception as e:
        logger.error(f"Terjadi kesalahan dalam analyze_image: {e}", exc_info=True) # Log error dengan traceback lengkap
        await processing_message.delete() # Pastikan pesan dihapus bahkan saat error
        await update.message.reply_text("⚠️ Maaf, terjadi kesalahan saat menganalisis gambar Anda. Silakan coba lagi nanti.")
    finally:
        if os.path.exists('user_image.jpg'):
            os.remove('user_image.jpg')

async def main():
    """Fungsi utama untuk menjalankan bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    photo_handler = MessageHandler(filters.PHOTO, analyze_image)
    application.add_handler(photo_handler)

    logger.info("Bot Telegram sudah berjalan...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
