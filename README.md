# WhatsApp YouTube to MP3 Downloader

Este projeto é uma aplicação Flask que permite aos usuários baixar vídeos do YouTube e convertê-los em arquivos MP3 via WhatsApp. Utiliza a API do Twilio para interagir com os usuários e o `yt-dlp` para realizar o download dos vídeos.

## Funcionalidades

- **Cadastro de Usuários**: Os usuários podem se cadastrar enviando seu nome.
- **Download de Vídeos**: Envie um link do YouTube e o aplicativo baixará o vídeo como um arquivo MP3.
- **Listagem de Arquivos**: Os usuários podem listar os arquivos MP3 disponíveis para download.
- **Respostas Interativas**: O aplicativo responde às mensagens dos usuários e confirma os nomes.

## Requisitos

Antes de executar o projeto, certifique-se de ter os seguintes requisitos instalados:

- Python 3.x
- Flask
- Twilio
- yt-dlp
- moviepy
- outros pacotes requeridos no `requirements.txt`

## Configuração

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu_usuario/seu_repositorio.git
   cd seu_repositorio

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt

3. Configure as credenciais do Twilio:

    No arquivo, defina suas credenciais do Twilio:

   ```python
   account_sid = 'SEU_ACCOUNT_SID'
   auth_token = 'SEU_AUTH_TOKEN'
   twilio_whatsapp_number = 'SEU_NUMERO_WHATSAPP',

4. Crie um arquivo user_names.json no diretório raiz do projeto para armazenar os nomes dos usuários. O arquivo pode ser inicializado vazio:

    ```json
    {}

5. Execute a aplicação:

    ```bash
    python app.py

A aplicação estará disponível em http://127.0.0.1:9000.

# Uso
- Adicione o número do WhatsApp do Twilio aos seus contatos.
- Envie uma mensagem para o número do WhatsApp.
- Siga as instruções fornecidas pelo bot para se cadastrar e utilizar as funcionalidades.

# Estrutura do Projeto

   ```bash
      whatsapp_youtube_to_mp3/
      │
      ├── app.py                   # Código principal da aplicação
      ├── user_names.json          # Armazenamento dos nomes dos usuários
      ├── requirements.txt         # Dependências do projeto
      └── files/                   # Diretório onde os arquivos MP3 serão armazenados






     
