import discord
from discord import app_commands
from discord.ext import tasks
import config
import bot_commands
from sqlite_client import SQLiteClient

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tasks.loop(seconds=10)
async def check_market():
    ...

@client.event
async def on_ready():
    if not check_market.is_running():
        check_market.start()
    print(f'"{client.user}" としてログインしました')
    try:
        await tree.sync()
        print("スラッシュコマンドを同期しました。")
    except Exception as e:
        print(f"コマンドの同期中にエラーが発生しました: {e}")

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if not message.content.startswith(f"<@{client.user.id}>"):
        return

    content_after_mention = message.content.replace(f"<@{client.user.id}>", "")

    if message.author.id in config.Discord.Admins:
        if content_after_mention == "kill":
            print("シャットダウンコマンドを受け取りました。")
            await client.close()
            return

def main():
    bot_commands.setup(tree)
    client.run(config.Discord.Token)

if __name__ == "__main__":
    main()
