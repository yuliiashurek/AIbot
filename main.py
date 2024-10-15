import openai
import configparser
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Load tokens from the token.ini file
config = configparser.ConfigParser()
config.read('token.ini')

TELEGRAM_TOKEN = config.get('API_KEYS', 'TELEGRAM_TOKEN')
OPENAI_TOKEN = config.get('API_KEYS', 'OPENAI_TOKEN')


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Student", callback_data='student')],
        [InlineKeyboardButton("It-technologies", callback_data='it-technologies')],
        [InlineKeyboardButton("Contacts", callback_data='contacts')],
        [InlineKeyboardButton("ChatGpt", callback_data='chatgpt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['chat_mode'] = False
    if update.callback_query:
        await update.callback_query.message.edit_text("Choose an option:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Choose an option:", reply_markup=reply_markup)


class AIbot:
    def __init__(self, token, openai_token):
        self.application = ApplicationBuilder().token(token).build()
        openai.api_key = openai_token
        self.user_conversations = {}  # Store conversations per user

    def start(self):
        self.application.add_handler(CommandHandler("start", self.reset_conversation))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_user_input))  # Handle user text input
        self.application.run_polling()

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'student':
            text = "Шурек Юлія, ІА-11"
        elif query.data == 'it-technologies':
            text = "Основи WEB-технологій"
        elif query.data == 'contacts':
            text = "@juliysik"
        elif query.data == 'chatgpt':
            await self.start_chatgpt_conversation(update, context)
            text = "Hello, what would you like to ask?"
        elif query.data == 'back':
            await show_main_menu(update, context)
            return
        else:
            text = "Unknown option."

        keyboard = [[InlineKeyboardButton("Back", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=text, reply_markup=reply_markup)

    async def start_chatgpt_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.callback_query.from_user.id
        self.user_conversations[user_id] = []

        context.user_data['chat_mode'] = True
        await update.callback_query.message.edit_text("Hello, what would you like to ask?")

    async def handle_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id

        if context.user_data.get('chat_mode'):
            user_message = update.message.text
            self.user_conversations[user_id].append({"role": "user", "content": user_message})

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=self.user_conversations[user_id]
                )

                bot_message = response.choices[0].message.content
                self.user_conversations[user_id].append({"role": "assistant", "content": bot_message})

                await update.message.reply_text(bot_message)
            except Exception as e:
                await update.message.reply_text("There was an error processing your request. Please try again later.")
                print(f"Error: {e}")
        else:
            await update.message.reply_text("You are not in chat mode. Please select 'ChatGpt' first.")

    async def reset_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]

        await show_main_menu(update, context)


if __name__ == '__main__':
    bot = AIbot(TELEGRAM_TOKEN, OPENAI_TOKEN)
    bot.start()
