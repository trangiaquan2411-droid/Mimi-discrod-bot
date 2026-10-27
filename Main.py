import os
import discord

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Đã đăng nhập thành công với tên {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('hello'):
        await message.channel.send('Xin chào! Tôi là Mimi bot đây.')

client.run(os.environ.get('DISCORD_TOKEN'))
