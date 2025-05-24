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

# Ambil kunci API OpenAI dari variabel lingkungan
# PENTING: Kunci OpenAI harus dimulai dengan 'sk-', pastikan ini adalah kunci OpenAI yang valid.
# Ganti 'YOUR_OPENAI_API_KEY' dengan nama variabel lingkungan yang Anda gunakan
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AIzaSyAFddWRTXHkulEBpIjbcO2pUXx2lvGOXro")


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menangani pesan yang berisi gambar.
    Mengirim gambar ke Gemini untuk analisis, lalu menggunakan hasilnya
    untuk membuat prompt ke GPT-4, dan mengirimkan balasan ke pengguna.
    """
    photo_path = None # Inisialisasi photo_path untuk memastikan dihapus di finally
    try:
        # 1. Mengunduh gambar dari Telegram
        # Mengambil file foto dengan resolusi tertinggi (indeks terakhir)
        photo_file = await update.message.photo[-1].get_file()
        # Mengunduh file ke drive lokal
        photo_path = await photo_file.download_to_drive()
        await update.message.reply_text("Gambar diterima! Sedang menganalisis...")

        # 2. Mengirim gambar ke Google Gemini Vision API
        # Membaca gambar dalam mode binary dan meng-encode ke Base64
        with open(photo_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        # URL endpoint Gemini API untuk generateContent (vision)
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        # Payload untuk Gemini API
        # Menggunakan inlineData untuk mengirim gambar Base64
        # Prompt awal untuk Gemini agar menganalisis gambar sebagai chart keuangan
        gemini_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Analisis gambar chart keuangan ini. Identifikasi sinyal (misalnya, bullish, bearish, netral) dan pola teknikal (misalnya, head and shoulders, double top, support/resistance, tren) yang terlihat. Jelaskan secara ringkas dan profesional."},
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
        gemini_analysis_text = "Tidak dapat menganalisis gambar."
        if gemini_data and gemini_data.get('candidates'):
            first_candidate = gemini_data['candidates'][0]
            if first_candidate.get('content') and first_candidate['content'].get('parts'):
                first_part = first_candidate['content']['parts'][0]
                if first_part.get('text'):
                    gemini_analysis_text = first_part['text']

        await update.message.reply_text("Analisis Gemini selesai. Sekarang meminta penjelasan dari GPT-4...")

        # 3. Mengirim hasil analisis Gemini ke OpenAI GPT-4 API
        gpt4_url = "https://api.openai.com/v1/chat/completions"

        # Prompt untuk GPT-4, menggunakan hasil analisis dari Gemini
        prompt_to_gpt4 = (
            f"Berdasarkan analisis chart keuangan berikut dari Gemini:\n\n"
            f"{gemini_analysis_text}\n\n"
            f"Berikan 3 alasan teknikal yang singkat dan profesional untuk sinyal yang teridentifikasi. "
            f"Sertakan juga prediksi sinyal (misalnya, Bullish, Bearish, Netral) di awal jawaban Anda."
        )

        # Melakukan POST request ke GPT-4 API
        gpt4_response = requests.post(
            gpt4_url,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o", # Menggunakan model yang lebih baru dan mampu (atau tetap gpt-4)
                "messages": [{"role": "user", "content": prompt_to_gpt4}],
                "temperature": 0.7,
                "max_tokens": 500 # Batasi panjang respons GPT-4
            },
            timeout=30 # Tingkatkan timeout
        )

        # Memeriksa status HTTP dari respons GPT-4
        gpt4_response.raise_for_status()
        gpt4_data = gpt4_response.json()

        # Ekstraksi respons dari GPT-4
        reasons = "Tidak dapat menghasilkan alasan."
        if gpt4_data and gpt4_data.get('choices'):
            first_choice = gpt4_data['choices'][0]
            if first_choice.get('message') and first_choice['message'].get('content'):
                reasons = first_choice['message']['content']

        # 4. Mengirim balasan ke pengguna Telegram
        reply = f"📊 Analisis Chart:\n\n{reasons}"
        await update.message.reply_text(reply)

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
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY tidak ditemukan. Harap atur variabel lingkungan.")
    
    if TELEGRAM_BOT_TOKEN and GEMINI_API_KEY and OPENAI_API_KEY:
        main()
    else:
        print("Bot tidak dapat dimulai karena ada kunci API yang hilang.")

