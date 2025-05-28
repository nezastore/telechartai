import os
import requests
import base64
from telegram import Update
from telegram.ext import ContextTypes

# Token Telegram dan API Gemini (jangan lupa ganti dengan milik Anda)
TELEGRAM_BOT_TOKEN = "7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA"
GEMINI_API_KEY = "AIzaSyAFddWRTXHkulEBpIjbcO2pUXx2lvGOXro"

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Menangani pesan yang berisi gambar.
    Mengirim gambar ke Gemini untuk analisis dan langsung mendapatkan sinyal serta alasan.
    Membalas dengan teks yang sudah diformat Markdown dan emoji.
    """
    photo_path = None
    try:
        # Ambil file gambar terakhir yang dikirim user
        photo_file = await update.message.photo[-1].get_file()
        photo_path = await photo_file.download_to_drive()
        await update.message.reply_text("📷 Gambar diterima! Sedang menganalisis menggunakan NEZATRADE...")

        # Baca dan encode gambar ke Base64
        with open(photo_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        # URL endpoint Gemini API dengan API key
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        # Payload dengan instruksi analisis dan gambar encoded
        gemini_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": (
                            "Anda adalah seorang analis teknikal pasar keuangan. Analisis ini bersifat Profesional dan Tingkat kecerdasan Program.\n\n"
                            "Analisis screenshot chart trading berikut ini secara detail. Fokus pada elemen-elemen berikut jika terlihat dengan jelas di gambar:\n"
                            "1. Perkiraan Harga Saat Ini: (jika ada skala harga yang jelas dan mudah dibaca).\n"
                            "2. Tren Utama: (Contoh: Naik, Turun, Sideways/Konsolidasi).\n"
                            "3. Pola Candlestick/Chart Signifikan: (Contoh: Doji di Puncak/Lembah, Engulfing, Hammer, Shooting Star, Head and Shoulders, Double Top/Bottom, Triangle, Flag, Wedge, Channel).\n"
                            "4. Kondisi Indikator Teknikal Utama (jika terlihat jelas): (Contoh: RSI (Oversold <30, Overbought >70, Divergence), MACD (Golden/Death Cross, Divergence, Posisi Histogram), Moving Averages (Posisi harga terhadap MA, Golden/Death Cross MA), Bollinger Bands (Harga menyentuh upper/lower band, Squeeze)).\n"
                            "5. Level Support dan Resistance Kunci: (Identifikasi beberapa level S&R penting yang terlihat).\n\n"
                            "6. Gunakan strategi Pola 7 Candle & Teknik 7 Naga.\n"
                            "Berdasarkan semua observasi di atas, berikan:\n"
                            "🔹 **Saran Trading Keseluruhan:** (BUY, SELL, atau NETRAL/WAIT)\n"
                            "🔹 **Alasan Utama (poin-poin):** (Berikan minimal 2-3 alasan utama untuk saran trading Anda, merujuk pada observasi dari poin 1-6 di atas).\n"
                            "🔹 **Potensi Level Penting (jika teridentifikasi dari chart):**\n"
                            "   - 🟢 Open Posisi potensial: [jika ada]\n"
                            "   - 🎯 Target Profit (TP) potensial: [jika ada]\n"
                            "   - 🛑 Stop Loss (SL) potensial: [jika ada]\n\n"
                            "Struktur jawaban Anda sebaiknya jelas, terperinci, dan menggunakan tampilan yang keren atau point setiap bagian."
                        )},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": encoded_image
                            }
                        }
                    ]
                }
            ]
        }

        # Kirim request ke Gemini API
        gemini_response = requests.post(
            gemini_url,
            json=gemini_payload,
            timeout=30
        )
        gemini_response.raise_for_status()
        gemini_data = gemini_response.json()

        # Default pesan jika gagal mendapatkan hasil
        final_reply_text = "⚠️ Tidak dapat menganalisis gambar atau menghasilkan prediksi."

        # Ambil hasil analisis dari response Gemini
        if gemini_data and gemini_data.get('candidates'):
            first_candidate = gemini_data['candidates'][0]
            if first_candidate.get('content') and first_candidate['content'].get('parts'):
                first_part = first_candidate['content']['parts'][0]
                if first_part.get('text'):
                    raw_text = first_part['text']

                    # Pemrosesan teks untuk menambahkan emoji dan format Markdown
                    replacements = {
                        "BUY": "🟢 **BUY**",
                        "SELL": "🔴 **SELL**",
                        "TP": "🎯 **TP**",
                        "SL": "🛑 **SL**",
                        "Open Posisi": "🟢 **Open Posisi**",
                        "Target Profit": "🎯 **Target Profit**",
                        "Stop Loss": "🛑 **Stop Loss**",
                        "Saran Trading": "💡 **Saran Trading**",
                        "Alasan": "📌 **Alasan**",
                        "Potensi Level Penting": "📊 **Potensi Level Penting**",
                    }
                    processed_text = raw_text
                    for key, val in replacements.items():
                        processed_text = processed_text.replace(key, val)

                    # Tambahkan baris kosong antar paragraf untuk keterbacaan
                    processed_text = processed_text.replace("\n\n", "\n\n")

                    final_reply_text = processed_text

        # Kirim balasan dengan parse_mode Markdown agar format tampil
        await update.message.reply_text(final_reply_text, parse_mode='Markdown')

    except requests.exceptions.RequestException as req_err:
        await update.message.reply_text(f"❌ Terjadi masalah koneksi atau API: {req_err}. Pastikan kunci API dan URL benar.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Terjadi kesalahan: {str(e)}. Mohon coba lagi.")
    finally:
        # Hapus file gambar yang sudah diunduh
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"File {photo_path} telah dihapus.")
