from flask import Flask, request, send_from_directory
from twilio.rest import Client
import json
import os
import re
import unicodedata
from moviepy.editor import AudioFileClip
import yt_dlp

app = Flask(__name__)

account_sid = ''
auth_token = ''
twilio_whatsapp_number = ''


client = Client(account_sid, auth_token)

def load_user_names(filename='user_names.json'):
    """Carrega os nomes de usuários de um arquivo JSON."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

def save_user_names(user_names, filename='user_names.json'):
    """Salva os nomes de usuários em um arquivo JSON."""
    with open(filename, 'w') as file:
        json.dump(user_names, file)

# Armazenar nomes de usuários por número
user_names = load_user_names()

def sanitize_filename(filename, max_length=25):
    """Normaliza e sanitiza o nome do arquivo removendo caracteres especiais."""
    normalized = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    sanitized = re.sub(r'[^\w\s-]', '', normalized)  # Remove caracteres especiais
    sanitized = re.sub(r'\s+', '-', sanitized).lower()  # Substitui espaços por hífens e converte para minúsculas
    sanitized = sanitized[:max_length]  # Limita o tamanho
    if not sanitized.endswith('.mp3'):
        sanitized += '.mp3'  # Garante que termine com .mp3
    return sanitized

def download_youtube_video(url, output_path='files'):
    """Faz o download do vídeo do YouTube e retorna o caminho do arquivo."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return os.path.join(output_path, f"{info_dict['title']}.{info_dict['ext']}")

def convert_to_mp3(file_path):
    """Converte o arquivo de áudio para MP3."""
    mp3_file = file_path.rsplit('.', 1)[0] + '.mp3'
    audio = AudioFileClip(file_path)
    audio.write_audiofile(mp3_file, codec='mp3')
    audio.close()
    return mp3_file

def list_mp3_files(directory='files'):
    """Lista os arquivos MP3 disponíveis no diretório especificado."""
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.endswith('.mp3')]

@app.route('/files/<path:filename>', methods=['GET'])
def send_file(filename):
    """Rota para enviar arquivos MP3 do diretório 'files'."""
    return send_from_directory('files', filename)

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Rota para listar os usuários armazenados."""
    if user_names:
        usuarios = "\n".join([f"{num + 1}. {name} ({num})" for num, name in enumerate(user_names.values())])
        response = f"Usuários armazenados:\n{usuarios}"
    else:
        response = "Nenhum usuário armazenado."

    return response, 200

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """Responde às mensagens do WhatsApp."""
    incoming_msg = request.form.get('Body').strip()
    sender = request.form.get('From')

    # Verifica se o nome do usuário já está armazenado
    if sender not in user_names:
        if incoming_msg.lower() == 'sair':
            client.messages.create(
                body="😊 **Até mais!** Se precisar, é só chamar!",
                from_=twilio_whatsapp_number,
                to=sender
            )
            return '', 200
        # Solicita o nome do usuário
        user_names[sender] = None  # Inicializa o nome como None
        client.messages.create(
            body="👋 Olá! Qual é o seu nome?",
            from_=twilio_whatsapp_number,
            to=sender
        )
        return '', 200

    # Se o nome já estiver armazenado
    user_name = user_names[sender]

    if user_name is None:
        # Armazena temporariamente o nome do usuário para confirmação
        client.messages.create(
            body=f"Você digitou: *{incoming_msg}*. Confirme se está correto (sim/não).",
            from_=twilio_whatsapp_number,
            to=sender
        )
        user_names[sender] = {'temp_name': incoming_msg.strip(), 'confirmed': False}
        return '', 200

    if isinstance(user_name, dict) and not user_name.get('confirmed', False):
        # Verifica se o usuário confirmou o nome
        if incoming_msg.lower() == 'sim':
            # Salva o nome e marca como confirmado
            user_names[sender] = user_name['temp_name']
            save_user_names(user_names)  # Salvar após confirmar
            client.messages.create(
                body=f"🌟 *Bem-vindo ao nosso serviço, {user_names[sender]}!* 🌟\n\n"
                     "🎶 Para começar, você pode:\n"
                     "1. Enviar um link do YouTube para baixar o vídeo como MP3.\n"
                     "2. Digitar 'listar' para ver os arquivos MP3 disponíveis.\n",
                     
                from_=twilio_whatsapp_number,
                to=sender
            )
        elif incoming_msg.lower() == 'não':
            # Reinicia o processo de cadastro
            user_names[sender] = None
            client.messages.create(
                body="Ok, vamos tentar novamente. Qual é o seu nome?",
                from_=twilio_whatsapp_number,
                to=sender
            )
        else:
            # Caso o usuário não tenha respondido sim ou não
            client.messages.create(
                body="Por favor, responda com 'sim' para confirmar ou 'não' para corrigir.",
                from_=twilio_whatsapp_number,
                to=sender
            )
        return '', 200

    if incoming_msg.lower().startswith('http'):
        output_directory = 'files'
        try:
            # Informar o usuário sobre o download
            client.messages.create(
                body=f"{user_name}, estamos baixando seu vídeo...",
                from_=twilio_whatsapp_number,
                to=sender
            )
            downloaded_file = download_youtube_video(incoming_msg, output_directory)

            # Informar sobre a conversão
            client.messages.create(
                body=f"{user_name}, estamos convertendo seu video para MP3...",
                from_=twilio_whatsapp_number,
                to=sender
            )
            mp3_file = convert_to_mp3(downloaded_file)

            # Renomear o arquivo MP3
            sanitized_name = sanitize_filename(os.path.basename(mp3_file))
            new_mp3_file_path = os.path.join(output_directory, sanitized_name)
            os.rename(mp3_file, new_mp3_file_path)

            # Criar URL para envio
            media_url = f'https://4c63-2804-7f0-b2c0-40a-88f6-38d2-5844-fc7.ngrok-free.app/files/{sanitized_name}'

            # Enviar o MP3
            client.messages.create(
                body=f"{user_name}, enviando o arquivo MP3...",
                from_=twilio_whatsapp_number,
                to=sender,
                media_url=media_url
            )
        except Exception as e:
            # Informar sobre o erro
            client.messages.create(
                body=f'Ocorreu um erro: {str(e)}',
                from_=twilio_whatsapp_number,
                to=sender
            )
    elif incoming_msg.lower() == 'listar':
        # Listar arquivos MP3
        mp3_files = list_mp3_files()
        if mp3_files:
            response = "📁 *Arquivos MP3 disponíveis:*\n" + "\n".join([f"{i + 1}. {file}" for i, file in enumerate(mp3_files)])
        else:
            response = "🚫 **Nenhum arquivo MP3 disponível.**\n\n"
        response += " (envie um link do YouTube para baixar mais vídeos como MP3)"
    
        client.messages.create(
            body=f"{user_name}, {response}",
            from_=twilio_whatsapp_number,
            to=sender
        )
    elif incoming_msg.isdigit():
        # Enviar o arquivo MP3 com base no índice fornecido
        index = int(incoming_msg) - 1
        mp3_files = list_mp3_files()
        if 0 <= index < len(mp3_files):
            mp3_file = mp3_files[index]
            media_url = f'https://4c63-2804-7f0-b2c0-40a-88f6-38d2-5844-fc7.ngrok-free.app/files/{mp3_file}'
            client.messages.create(
                body=f"{user_name}, enviando o arquivo: {mp3_file}",
                from_=twilio_whatsapp_number,
                to=sender,
                media_url=media_url
            )
        else:
            client.messages.create(
                body=f"{user_name}, número inválido. Por favor, forneça um número da lista de arquivos MP3.",
                from_=twilio_whatsapp_number,
                to=sender
            )
    else:
        # Mensagem padrão
        client.messages.create(
            body=(f"🌟 **Bem-vindo ao nosso serviço, {user_name}!** 🌟\n\n"
                  "🎶 **Envie um link do YouTube** para baixar o vídeo como MP3, ou digite **'listar'** "
                  "para ver os arquivos MP3 disponíveis. 📂\n\n"
                  "Estamos aqui para ajudar! 😊\n\n"),
            from_=twilio_whatsapp_number,
            to=sender
        )

    return '', 200

if __name__ == '__main__':
    app.run(debug=True, port=9000)
