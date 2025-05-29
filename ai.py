import telegram
from telegram.ext import Application, MessageHandler, ContextTypes
# Mengimpor filters secara eksplisit dari telegram.ext.filters
from telegram.ext import filters
import google.generativeai as genai
import logging
import os

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
# Menggunakan model 'gemini-pro-vision' untuk kemampuan pemahaman gambar
model = genai.GenerativeModel('gemini-pro-vision')

# Prompt analisis yang akan dikirimkan ke Gemini AI bersama dengan gambar
ANALYSIS_PROMPT = """Anda adalah seorang analis teknikal pasar forex. Analisis ini bersifat Profesional dan Tingkat kecerdasan Program.\n\nAnalisis screenshot chart trading berikut ini secara detail. Fokus pada elemen-elemen candle terakhir berikut jika terlihat dengan jelas di gambar:\n1. Perkiraan Harga Saat Ini: (jika ada skala harga yang jelas dan mudah dibaca).\n2. Tren Utama: (Contoh: Naik, Turun, Sideways/Konsolidasi).\n3. Pola Candlestick/Chart Signifikan: (Contoh: Doji di Puncak/Lembah, Engulfing, Hammer, Shooting Star, Head and Shoulders, Double Top/Bottom, Triangle, Flag, Wedge, Channel).\n4. Kondisi Indikator Teknikal Utama (jika terlihat jelas): (Contoh: RSI (Oversold <30, Overbought >70, Divergence), MACD (Golden/Death Cross, Divergence, Posisi Histogram), Moving Averages (Posisi harga terhadap MA, Golden/Death Cross MA), Bollinger Bands (Harga menyentuh upper/lower band, Squeeze)).\n5. Level Support dan Resistance Kunci: (Identifikasi beberapa level S&R penting yang terlihat).\n\n6. Gunakan strategi Pola 7 Candle & Teknik 7 Naga.\nBerdasarkan semua observasi di atas, berikan:\n🔹 **Saran Trading Keseluruhan:** (BUY, SELL, atau NETRAL/WAIT)\n🔹 **Alasan Utama (poin-poin):** (Berikan minimal 2-3 alasan utama untuk saran trading Anda, merujuk pada observasi dari poin 1-6 di atas).\n🔹 **Potensi Level Penting (jika teridentifikasi dari chart):**\n  - 🟢 Open Posisi potensial: [jika ada]\n  - 🎯 Target Profit (TP) potensial: [jika ada]\n  - 🛑 Stop Loss (SL) potensial: [jika ada]\n\nStruktur jawaban Anda sebaiknya jelas, terperinci, dan menggunakan tampilan yang keren atau point setiap bagian."""

async def analyze_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menganalisis gambar yang dikirimkan pengguna menggunakan AI.
    Respons dari AI kemudian diformat agar terlihat lebih menarik
    dengan tambahan emotikon dan Markdown.
    """
    user = update.message.from_user
    # Mengambil objek foto dengan resolusi tertinggi
    photo = update.message.photo[-1]
    # Mendapatkan objek file dari Telegram API
    file = await context.bot.get_file(photo.file_id)
    # Mengunduh gambar ke penyimpanan lokal
    await file.download_to_drive('user_image.jpg')
    logger.info("Gambar diterima dari %s", user.first_name)

    # Mengirim pesan "Sedang menganalisis..." agar pengguna tahu bot sedang bekerja
    processing_message = await update.message.reply_text("⏳ Sedang menganalisis gambar Anda... Mohon tunggu sebentar.")

    try:
        # Membaca data gambar dalam mode biner
        with open('user_image.jpg', 'rb') as image_file:
            image_data = image_file.read()

        # Menyiapkan konten untuk dikirim ke Gemini AI (gambar dan teks prompt)
        contents = [
            {"mime_type": "image/jpeg", "data": image_data},
            {"text": ANALYSIS_PROMPT}
        ]

        # Memanggil Gemini AI untuk menghasilkan konten berdasarkan gambar dan prompt
        response = await model.generate_content(contents)
        # Mengambil teks analisis dari respons Gemini
        analysis_text = response.text.strip()
        # Memisahkan teks analisis menjadi baris-baris
        analysis_lines = analysis_text.split('\n')

        # Membangun respons yang diformat dengan emotikon dan Markdown
        formatted_response = "📈 **Analisis Trading Profesional** 📉\n\n"
        for line in analysis_lines:
            # Menambahkan emotikon berdasarkan isi baris
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
                # Menghilangkan "🔹 **" dan ":**" untuk pemformatan yang lebih bersih
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
                # Untuk baris lain yang tidak cocok dengan pola di atas
                formatted_response += f"{line}\n"

        # Menghapus pesan "Sedang menganalisis..."
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=processing_message.message_id)
        # Mengirim respons analisis yang sudah diformat ke pengguna
        await update.message.reply_text(formatted_response, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Terjadi kesalahan saat memproses gambar: {e}")
        # Menghapus pesan "Sedang menganalisis..." jika terjadi error
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=processing_message.message_id)
        await update.message.reply_text("Maaf, terjadi kesalahan saat menganalisis gambar. Pastikan gambar chart jelas.")
    finally:
        # Selalu menghapus file gambar setelah diproses, baik berhasil atau gagal
        if os.path.exists('user_image.jpg'):
            os.remove('user_image.jpg')

async def main():
    """Fungsi utama untuk menjalankan bot."""
    # Membangun aplikasi bot Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Menambahkan handler untuk pesan yang berisi foto
    # Menggunakan filters.PHOTO dari modul filters yang baru diimpor
    photo_handler = MessageHandler(filters.PHOTO, analyze_image)
    application.add_handler(photo_handler)

    # Menjalankan bot dalam mode polling, menunggu pesan masuk
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    # Menjalankan fungsi main secara asinkron
    asyncio.run(main())
