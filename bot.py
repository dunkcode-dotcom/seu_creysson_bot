from dotenv import load_dotenv
import logging
import os
import requests
import sys
import easyocr
import numpy as np
from PIL import Image
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from io import BytesIO
import re

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Substitua pelo seu token real
BOT_TOKEN = os.getenv('BOT_TOKEN')
URL_TELEGRAM_GETME = os.getenv('URL_TELEGRAM_GETME')
CAMINHO_TESSERACT = os.getenv('CAMINHO_TESSERACT')

if not BOT_TOKEN:
    raise ValueError("A variável de ambiente BOT_TOKEN não está definida!")

# URL para validar o token
URL = f"{URL_TELEGRAM_GETME}{BOT_TOKEN}/getMe"

# Função para validar o token
def validar_token():
    try:
        response = requests.get(URL)
        data = response.json()

        if data.get("ok"):
            print("✅ Token válido! Bot iniciado...")
        else:
            print("❌ Token inválido! Verifique o seu token e tente novamente.")
            sys.exit(1)  # Encerra o programa com erro
    except requests.RequestException as e:
        print(f"❌ Erro ao validar o token: {e}")
        sys.exit(1)

# Função para verificar se o caminho do Tesseract está correto
def verificar_tesseract():
    try:
        # Teste se o Tesseract está funcionando corretamente
        pytesseract.pytesseract.tesseract_cmd = CAMINHO_TESSERACT # Atualize para o caminho correto
        test_text = pytesseract.image_to_string('photo_teste.jpg')  # Usando uma imagem de teste
        print("✅ Tesseract está funcionando corretamente.")
    except pytesseract.pytesseract.TesseractNotFoundError:
        print("❌ Erro: Tesseract não encontrado. Verifique a instalação e o caminho.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao executar o Tesseract: {e}")
        sys.exit(1)

# Função para ler o texto do comprovante (imagem) usando o EasyOCR
def ler_comprovante_easyocr(image_data):
    """Usa o EasyOCR para ler texto de uma imagem e retorna um resumo filtrado."""
    # Converter os dados de imagem em um formato que o EasyOCR entenda
    image = Image.open(BytesIO(image_data))
    image_np = np.array(image)  # Converte para numpy array
    
    # Inicializa o leitor EasyOCR
    reader = easyocr.Reader(['pt', 'en'])  # Suporta vários idiomas
    result = reader.readtext(image_np)

    # Extrai o texto detectado
    texto = " ".join([res[1] for res in result])

    # Filtra os dados relevantes com base em palavras-chave e regex
    dados_resumo = filtrar_dados(texto)
    
    return dados_resumo

def filtrar_dados(texto):
    """Filtra os dados de favorecido, pagador e vencimento do texto extraído."""
    dados = {
        "favorecido": None,
        "pagador": None,
        "vencimento": None
    }
    
    # Regex para identificar o favorecido, pagador e vencimento
    favorecido_regex = r"Favorecido\s*[:\-]?\s*([a-zA-Z\s]+)"
    pagador_regex = r"Pagador\s*[:\-]?\s*([a-zA-Z\s]+)"
    vencimento_regex = r"Vencimento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})"
    
    # Buscando os dados com regex
    favorecido = re.search(favorecido_regex, texto, re.IGNORECASE)
    if favorecido:
        dados["favorecido"] = favorecido.group(1).strip()
    
    pagador = re.search(pagador_regex, texto, re.IGNORECASE)
    if pagador:
        dados["pagador"] = pagador.group(1).strip()
    
    vencimento = re.search(vencimento_regex, texto, re.IGNORECASE)
    if vencimento:
        dados["vencimento"] = vencimento.group(1).strip()
    
    # Montando o resumo
    resumo = "\n".join([f"{key.capitalize()}: {value}" for key, value in dados.items() if value])
    
    return resumo

# Função para tratar o comando /start
async def start(update: Update, context: CallbackContext) -> None:
    """Envia a mensagem de boas-vindas e exibe o menu."""
    keyboard = [["1. Enviar comprovante para imobiliária"], ["2. Sugestões"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Olá! Eu sou o Seu Creysson. Fui criado pra te ajudar a enviar o comprovante da imobiliária no dia certo, JÁ QUE TU ESQUECE."
    )
    await update.message.reply_text("Selecione o que deseja fazer agora:", reply_markup=reply_markup)

# Função para lidar com as respostas do menu
async def handle_response(update: Update, context: CallbackContext) -> None:
    """Responde com base na opção escolhida."""
    user_choice = update.message.text

    if "1. Enviar comprovante" in user_choice:
        await update.message.reply_text("Ótimo! Envie o comprovante como um arquivo ou foto.")
    elif "2. Sugestões" in user_choice:
        await update.message.reply_text("Manda aí sua sugestão que eu repasso pro pessoal!")
    else:
        await update.message.reply_text("Não entendi... escolha uma das opções do menu.")

# Função para processar o arquivo de imagem
async def processar_comprovante(update: Update, context: CallbackContext) -> None:
    """Processa a imagem enviada pelo usuário e extrai o texto do comprovante."""
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        image_data = await file.download_as_bytearray()

        dados_resumo = ler_comprovante_easyocr(image_data)  # Usando EasyOCR aqui

        if not dados_resumo:
            await update.message.reply_text("Não consegui ler ou filtrar as informações da imagem. Tente enviar uma imagem mais legível.")
        else:
            # Envia o resumo para o usuário
            await update.message.reply_text(
                f"Eu encontrei as seguintes informações no comprovante:\n\n{dados_resumo}"
                "\n\nEstá correto? Responda 'Sim' ou 'Não'."
            )
    else:
        await update.message.reply_text("Por favor, envie um arquivo ou imagem com o comprovante.")

# Função que confirma os dados
async def confirmar_comprovante(update: Update, context: CallbackContext) -> None:
    """Confirma os dados do comprovante."""
    texto = update.message.text.strip().lower()
    
    if texto == "sim":
        await update.message.reply_text("Comprovante confirmado! Enviado para a imobiliária.")
    elif texto == "não":
        await update.message.reply_text("Ok, por favor, envie novamente o comprovante.")
    else:
        await update.message.reply_text("Não entendi sua resposta. Por favor, responda 'Sim' ou 'Não'.")

# Configuração do bot
def main():
    """Inicializa e executa o bot."""
    validar_token()  # Valida o token antes de continuar
    #verificar_tesseract()  # Verifica se o Tesseract está configurado corretamente

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers (comandos e mensagens)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))
    app.add_handler(MessageHandler(filters.PHOTO, processar_comprovante))
    app.add_handler(MessageHandler(filters.TEXT, confirmar_comprovante))

    print("🤖 Bot rodando...")
    app.run_polling()

# Executa o bot
if __name__ == "__main__":
    main()
