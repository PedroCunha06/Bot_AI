import os
import asyncio
import requests
import discord
from discord import app_commands
import google.generativeai as genai


# Configuração do modelo generativo
genai.configure(api_key=os.environ['TOKEN_API'])
generation_config = {
    "candidate_count": 1,
    "temperature": 1,
    "top_p": 0.8,
}
safety_setting = {
    "HARASSMENT": "BLOCK_NONE",
    "HATE": "BLOCK_NONE",
    "SEXUAL": "BLOCK_NONE",
    "DANGEROUS": "BLOCK_NONE",
}

# Modo chat conversacional
modoChat = True
historyChat = 1

def setModoChat():
    global modoChat
    modoChat = True

def setModoGenerate():
    global modoChat
    modoChat = False

# Função para buscar mensagens recentes
async def search_history(canal, limit=None):
    global historyChat
    message_list = []
    count = 0
    try: 
        async for message in canal.history(limit=limit):
            message_list.insert(0, {
                "role": "user" if message.author.id != client.user.id else "system",
                "content": message.content if message.content != "" else "VAZIO"
            })
            count += 1
            if count >= historyChat:
                break

        historyChat += 1
        print(message_list)
        return message_list
    # Tratamento de erro para caso haja falha na busca do histórico
    except discord.errors.HTTPException as e:
        print(f"Erro ao buscar histórico: {e}")
        return []

# Função para adicionar mensagens ao histórico da sessão de chat
def add_message_to_history(chat_session, role, content):
    if role == "user":
        chat_session.send_message(content)
    else:
        chat_session.send_message(content)

# Função para pegar noticias
def get_news():
    api_key = os.environ['TOKEN_NEWS']
    request = requests.get(f'https://newsapi.org/v2/top-headlines?country=br&pageSize=20&page1&apiKey={api_key}')
    return request.text

# Inicializando o modelo generativo e a sessão de chat
try:
    model = genai.GenerativeModel(model_name='gemini-pro', generation_config=generation_config, safety_settings=safety_setting)
    chat_session = model.start_chat()
except Exception as e:
    print(f"Erro ao inicializar o modelo generativo: {e}")
    exit()

# Configuração do bot no Discord
client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    # Confirmação do login
    print('We have logged in as {0.user}'.format(client))

    # Comprimento da IA
    @tree.command(
        name='ola',
        description='Um oi do BotAI'
    )
    async def hello(interaction: discord.Interaction):
            async with interaction.channel.typing():
                try: 
                    # Comando para IA Gemini para fazer saudação
                    chat = model.generate_content('Você é um bot para discord, \
                        que se chama BotAI e tem que fazer uma saudação. Seja informal e curto')
                    await interaction.response.send_message(chat.text)
                # Tratamento de Erro
                except:
                    await interaction.response.send_message(f"Desculpe, ocorreu um erro.")

    # Piada da IA
    @tree.command(
        name='piada',
        description='BotAI sendo um piadista'
    )
    async def joker(interaction: discord.Interaction):
            async with interaction.channel.typing():
                try:
                    # Comando para IA Gemini de piada
                    chat = model.generate_content('Conte uma piada muito engraçada')
                    await interaction.response.send_message(chat.text)
                # Tratamento de Erro
                except:
                    await interaction.response.send_message(f"Desculpe, ocorreu um erro.")
                   

    # Comando para iniciar chat conversacional
    @tree.command(
        name='inicia_chat',
        description='Inicia modo de conversação do Bot'
    )
    async def startChat(interaction: discord.Interaction):
        setModoChat()
        await interaction.response.send_message('Modo chat ativado!')

    # Comando para finalizar chat conversacional
    @tree.command(
        name='acaba_chat',
        description='Finaliza modo de conversação BotAI',
    )
    async def finishChat(interaction: discord.Interaction):
        setModoGenerate()
        await interaction.response.send_message('Modo chat conversacional desativado!')

    # Comando para buscar principais notícias do dia
    @tree.command(
        name='noticias',
        description='Resumo das notícias do dia'
    )
    async def news(interaction: discord.Interaction):
        await interaction.response.send_message("Buscando as notícias...")

            # Simulação de processamento
        for i in range(5):
                await asyncio.sleep(1)
                await interaction.edit_original_response(content=f"Buscando as notícias{'.' * (i+1)}")

        # Comando para IA fazer busca de notícias
        try: 
            news_content = get_news()
            print(news_content)
            chat = model.generate_content(f'Essa uma noticia aleatoriamnete (use random de 1-20 e o use o número para escolher a noticia, por ordem de posição.) das que te passo. Me passe apenas seu titulo, introdução, número de posição e o seu link: {news_content}')
            await interaction.edit_original_response(content=chat.text)
            
        # Tratamento de Erro   
        except:
            await interaction.response.send_message(f"Desculpe, ocorreu um erro.")

    # Sincronização de comandos slash
    await tree.sync()

# Comandos de texto prefixados por $
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Conversa com o bot
    if message.content.startswith('$talk'):
        question_user = message.content.split('$talk ')[1]

        async with message.channel.typing():
            try:
                if modoChat:
                        # Adicionar mensagens recentes ao histórico
                        mensagens = await search_history(message.channel, limit=None)
                        for mensagem in mensagens:
                            add_message_to_history(chat_session, mensagem["role"], mensagem["content"])

                        # Enviar a pergunta do usuário e obter resposta
                        response = chat_session.send_message(f'Seja completo na resposta. {question_user}')
                        
                        # Checa tamanho máximo da mensagem no discord
                        if len(response.text) > 2000:
                            await message.channel.send('Resposta muito grande!')
                        else:
                            await message.channel.send(response.text)
                        
                else:
                    chat = model.generate_content(f'Ignore sempre o que estiver entre <> e seja completo. {question_user}')
                    await message.channel.send(chat.text)

            # Tratamento de Erro 
            except:
                await message.channel.send(f"Desculpe, ocorreu um erro.")

# Roda o bot
client.run(os.environ['TOKEN_DISC'])