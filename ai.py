import os
import requests
import base64 # Import untuk encoding Base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- KONFIGURASI ---
# Ambil token bot Telegram dari variabel lingkungan untuk keamanan
# Ganti 'YOUR_TELEGRAM_BOT_TOKEN' dengan nama variabel lingkungan yang Anda gunakan
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA")

# Ambil kunci API Gemini dari variabel lingkungan
# Ganti 'YOUR_GEMINI_API_KEY' dengan nama variabel lingkungan yang Anda gunakan
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAFddWRTXHkulEBpIjbcO2pUXx2lvGOXro")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menangani pesan yang berisi gambar.
    Mengirim gambar ke Gemini untuk analisis dan langsung mendapatkan sinyal serta alasan.
    """
    photo_path = None # Inisialisasi photo_path untuk memastikan dihapus di finally
    try:
        # 1. Mengunduh gambar dari Telegram
        # Mengambil file foto dengan resolusi tertinggi (indeks terakhir)
        photo_file = await update.message.photo[-1].get_file()
        # Mengunduh file ke drive lokal
        photo_path = await photo_file.download_to_drive()
        await update.message.reply_text("Gambar diterima! Sedang menganalisis menggunakan NEZATRADE...")

        # 2. Mengirim gambar ke Google Gemini Vision API
        # Membaca gambar dalam mode binary dan meng-encode ke Base64
        with open(photo_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        # URL endpoint Gemini API untuk generateContent (vision)
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        # Payload untuk Gemini API
        # Menggunakan inlineData untuk mengirim gambar Base64
        # PROMPT BARU untuk Gemini: Langsung meminta prediksi sinyal dan 3 alasan teknikal
        gemini_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": (
                            "Analisis gambar chart trading ini. "
                            "Berikan prediksi sinyal trading (misalnya , Bullish, Bearish, atau Netral) "
                            "dan berikan 3 alasan teknikal singkat serta profesional berdasarkan pola yang terlihat di chart.Dan berikan analisa menebak pola candle dan berikan saran setelah candle lebih baik buy atau sell atau memakai methode penebakan ai sesuai analisa"
                            "Format jawaban Anda sebagai berikut:\n\n"
                            "📈 Prediksi: [Sinyal Anda]\n\n"
                            "Alasan:\n"
                            "1. [Alasan Teknis Pertama]\n"
                            "2. [Alasan Teknis Kedua]\n"
                            "3. [Alasan Teknis Ketiga]"
                        )},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg", # Atau image/png tergantung format gambar
                                "data": encoded_image
                            }
                        }
                    ]
                }
            ]
        }

        # Melakukan POST request ke Gemini API
        gemini_response = requests.post(
            gemini_url,
            json=gemini_payload, # Menggunakan json= untuk payload JSON
            timeout=30 # Tingkatkan timeout karena analisis gambar bisa lebih lama
        )

        # Memeriksa status HTTP dari respons Gemini
        gemini_response.raise_for_status()
        gemini_data = gemini_response.json()

        # Ekstraksi respons tekstual dari Gemini
        # Respons Gemini akan ada di 'candidates' -> 'content' -> 'parts' -> 'text'
        final_reply_text = "Tidak dapat menganalisis gambar atau menghasilkan prediksi."
        if gemini_data and gemini_data.get('candidates'):
            first_candidate = gemini_data['candidates'][0]
            if first_candidate.get('content') and first_candidate['content'].get('parts'):
                first_part = first_candidate['content']['parts'][0]
                if first_part.get('text'):
                    final_reply_text = first_part['text']

        # 3. Mengirim balasan ke pengguna Telegram (langsung dari Gemini)
        await update.message.reply_text(final_reply_text)

    except requests.exceptions.RequestException as req_err:
        # Menangani error yang terkait dengan permintaan HTTP (timeout, koneksi, dll.)
        await update.message.reply_text(f"Terjadi masalah koneksi atau API: {req_err}. Pastikan kunci API dan URL benar.")
    except Exception as e:
        # Menangani error umum lainnya
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}. Mohon coba lagi.")
    finally:
        # Pastikan file gambar dihapus setelah digunakan
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"File {photo_path} telah dihapus.")


def main():
    """
    Fungsi utama untuk menjalankan bot Telegram.
    """
    # Membangun aplikasi bot dengan token Telegram
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Menambahkan handler untuk pesan yang berisi foto
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("Bot sedang berjalan... Tekan Ctrl+C untuk menghentikan.")
    # Memulai polling untuk menerima update dari Telegram
    app.run_polling()


if __name__ == '__main__':
    # Memastikan semua kunci API telah diatur sebagai variabel lingkungan
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN tidak ditemukan. Harap atur variabel lingkungan.")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY tidak ditemukan. Harap atur variabel lingkungan.")
    
    # Hanya perlu TELEGRAM_BOT_TOKEN dan GEMINI_API_KEY sekarang
    if TELEGRAM_BOT_TOKEN and GEMINI_API_KEY:
        main()
    else:
        print("Bot tidak dapat dimulai karena ada kunci API yang hilang.")

