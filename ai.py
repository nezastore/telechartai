import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, filters
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes

def handle_image(update: Update, context: CallbackContext):
    try:
        # Get image from Telegram
        photo_file = update.message.photo[-1].get_file()
        photo_path = photo_file.download()

        # Gemini AI 2.5 Flash API integration
        gemini_api_key = os.getenv('AIzaSyAFddWRTXHkulEBpIjbcO2pUXx2lvGOXro')
        gemini_url = "https://api.gemini.ai/v2.5-flash/analyze"
        
        with open(photo_path, "rb") as image_file:
            files = {"image": image_file}
            headers = {"Authorization": f"Bearer {gemini_api_key}"}
            
            gemini_response = requests.post(
                gemini_url,
                files=files,
                headers=headers,
                timeout=10  # Faster timeout for 2.5 Flash
            )
            
        gemini_data = gemini_response.json()
        
        # Extract signal and patterns
        signal = gemini_data.get('signal', 'N/A')
        patterns = ', '.join(gemini_data.get('patterns', ['Unknown']))

        # GPT-4 API integration for explanations
        gpt4_api_key = os.getenv('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')
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

        # Send response to user
        reply = f"📈 Prediksi: {signal}\n\nAlasan:\n{reasons}"
        update.message.reply_text(reply)
        
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")
        
def main():
    telegram_token = os.getenv('7899180208:AAH4hSC12ByLARkIhB4MXghv5vSYfPjj6EA')
    updater = Updater(telegram_token)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.photo, handle_image))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
