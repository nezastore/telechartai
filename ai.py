import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Token bot Telegram Anda (langsung pasang di sini)
TELEGRAM_BOT_TOKEN = "7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA"

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Ambil file foto dari pesan Telegram
        photo_file = await update.message.photo[-1].get_file()
        photo_path = await photo_file.download()  # download ke file lokal, dapatkan path file

        # Gemini AI 2.5 Flash API integration
        gemini_api_key = 'AIzaSyAFddWRTXHkulEBpIjbcO2pUXx2lvGOXro'  # Gunakan literal langsung sesuai permintaan
        gemini_url = "https://api.gemini.ai/v2.5-flash/analyze"
        
        with open(photo_path, "rb") as image_file:
            files = {"image": image_file}
            headers = {"Authorization": f"Bearer {gemini_api_key}"}
            
            gemini_response = requests.post(
                gemini_url,
                files=files,
                headers=headers,
                timeout=10
            )
            
        gemini_data = gemini_response.json()
        
        # Ambil sinyal dan pola dari response Gemini
        signal = gemini_data.get('signal', 'N/A')
        patterns = ', '.join(gemini_data.get('patterns', ['Unknown']))

        # GPT-4 API integration untuk penjelasan
        gpt4_api_key = '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'
        gpt4_url = "https://api.openai.com/v1/chat/completions"
        
        prompt = f"Berikan 3 alasan teknikal untuk sinyal {signal} berdasarkan pola berikut: {patterns}. Jelaskan secara singkat dan profesional."
        
        gpt4_response = requests.post(
            gpt4_url,
            headers={
                "Authorization": f"Bearer {gpt4_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        
        gpt4_data = gpt4_response.json()
        reasons = gpt4_data['choices'][0]['message']['content']

        # Kirim balasan ke user
        reply = f"📈 Prediksi: {signal}\n\nAlasan:\n{reasons}"
        await update.message.reply_text(reply)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Daftarkan handler untuk foto
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Jalankan bot
    app.run_polling()

if __name__ == '__main__':
    main()
