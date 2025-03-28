from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Defina seu token da API do Telegram
TOKEN = "COLOQUE_SEU_TOKEN_AQUI"

def start(update: Update, context: CallbackContext) -> None:
    """Responde ao comando /start com uma mensagem de boas-vindas e exibe o menu."""
    chat_id = update.message.chat_id
    
    # Mensagem de boas-vindas
    welcome_message = (
        "Olá! Eu sou o Seu Creysson. "
        "Fui criado pra te ajudar a enviar o comprovante da imobiliária no dia certo, "
        "JÁ QUE TU ESQUECE."
    )
    update.message.reply_text(welcome_message)
    
    # Exibe o menu
    menu_message = "Selecione o que deseja fazer agora:"
    keyboard = [["1. Enviar comprovante para imobiliária"], ["2. Sugestões"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    context.bot.send_message(chat_id=chat_id, text=menu_message, reply_markup=reply_markup)

def main():
    """Inicia o bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
