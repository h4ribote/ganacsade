import discord
from discord import app_commands, Embed, Color
from discord.ext import tasks
import config
import bot_commands
import marketplace
from sqlite_client import SQLiteClient
import asyncio
import traceback
import functools

intents = discord.Intents.default()
# intents.message_content = True # 必要に応じて
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# DBの初期化
db = SQLiteClient()
db.init_db()

# APIキーの取得
try:
    API_KEY = config.Torn.ApiKey
except AttributeError:
    API_KEY = marketplace.TORN_API_KEY

@tasks.loop(minutes=1) # 1分毎にチェック
async def check_market():
    # 通知チャンネルの取得
    channel_id_str = db.get_config("notification_channel_id")
    if not channel_id_str:
        return

    try:
        channel_id = int(channel_id_str)
        channel = client.get_channel(channel_id)
        if not channel:
             try:
                 channel = await client.fetch_channel(channel_id)
             except:
                 print(f"通知チャンネル(ID: {channel_id})が見つかりません。")
                 return
    except ValueError:
        return

    watches = db.get_all_watches()

    # watches is List[Tuple[int, int]] -> [(item_id, threshold), ...]
    loop = asyncio.get_running_loop()

    for item_id, threshold in watches:
        # APIコール待機 (レート制限考慮)
        await asyncio.sleep(10)

        try:
            # 非同期でデータを取得
            fetch_bazaar = functools.partial(marketplace.fetch_bazaar_data, item_id)
            fetch_market = functools.partial(marketplace.fetch_item_market_data, item_id, API_KEY)

            bazaar_data, market_listings = await asyncio.gather(
                loop.run_in_executor(None, fetch_bazaar),
                loop.run_in_executor(None, fetch_market)
            )

            bazaar_listings = bazaar_data.listings if bazaar_data else []
            all_listings = bazaar_listings + market_listings

            if not all_listings:
                continue

            cheapest = min(all_listings, key=lambda x: x.price)

            if cheapest.price <= threshold:
                # 通知
                item_name = db.get_item_name(item_id) or f"Item {item_id}"

                embed = Embed(title=f"Price Alert: {item_name}", color=Color.red())
                embed.description = f"目標価格 ${threshold:,} を下回りました！"
                embed.add_field(name="現在最安値", value=f"${cheapest.price:,}", inline=True)
                embed.add_field(name="ソース", value=cheapest.source, inline=True)
                embed.add_field(name="数量", value=f"{cheapest.quantity:,}", inline=True)
                if cheapest.source in ['Market', 'Bazaar']:
                    if cheapest.source == 'Market':
                        source_url = f"https://www.torn.com/page.php?sid=ItemMarket#/market/view=search&itemID={cheapest.item_id}"
                    else:
                        source_url = f"https://www.torn.com/bazaar.php?userId={cheapest.player_id}&itemId={cheapest.item_id}&highlight=1#/"
                    embed.add_field(name="URL", value=source_url, inline=False)

                await channel.send(embed=embed)
        except Exception as e:
            print(f"Error checking item {item_id}: {e}")
            continue

@client.event
async def on_ready():
    print(f'"{client.user}" としてログインしました')

    bot_commands.setup(tree, client, db, API_KEY)
    try:
        await tree.sync()
        print("スラッシュコマンドを同期しました。")
    except Exception as e:
        print(f"コマンドの同期中にエラーが発生しました: {e}")

    if not check_market.is_running():
        check_market.start()

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if not message.content.startswith(f"<@{client.user.id}>"):
        return

    content_after_mention = message.content.replace(f"<@{client.user.id}>", "").strip()

    try:
        if message.author.id in config.Discord.Admins:
            if content_after_mention == "kill":
                print("シャットダウンコマンドを受け取りました。")
                await client.close()
                return
    except AttributeError:
        pass

def main():
    try:
        client.run(config.Discord.Token)
    except AttributeError:
        print("Config error: Discord Token not found. Please check config.py")

if __name__ == "__main__":
    main()
