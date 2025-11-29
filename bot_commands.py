import discord
from discord import app_commands, Embed, Color, User, Interaction
from typing import Optional, List
import marketplace
from sqlite_client import SQLiteClient
import asyncio
import functools

def setup(tree: app_commands.CommandTree, client: discord.Client, db: SQLiteClient, api_key: str):

    @tree.command(name="price", description="アイテムの最安値を検索します")
    @app_commands.describe(item_name="検索するアイテム名")
    async def price(interaction: Interaction, item_name: str):
        await interaction.response.defer()

        loop = asyncio.get_running_loop()

        # 1. DB検索
        # DB operations are fast enough usually, but for strictness could be threaded too.
        # Keeping them sync for simplicity as per common simple bot patterns unless high load.
        item_id = db.get_item_id(item_name)

        # 2. DBになければAPIから全アイテム取得して更新 (APIキーがある場合)
        if not item_id:
            if api_key and api_key != "TORN_API_KEY":
                 # Run fetch_all_items in executor
                 items = await loop.run_in_executor(None, marketplace.fetch_all_items, api_key)
                 if items:
                     db.upsert_items(items)
                     item_id = db.get_item_id(item_name)

        if not item_id:
             await interaction.followup.send(f"アイテム '{item_name}' が見つかりませんでした。正確な名前を入力してください。", ephemeral=True)
             return

        official_name = db.get_item_name(item_id)

        # 3. データ取得 (並列実行)
        # Wrap synchronous calls
        fetch_bazaar = functools.partial(marketplace.fetch_bazaar_data, item_id)
        fetch_market = functools.partial(marketplace.fetch_item_market_data, item_id, api_key)

        bazaar_data, market_listings = await asyncio.gather(
            loop.run_in_executor(None, fetch_bazaar),
            loop.run_in_executor(None, fetch_market)
        )

        bazaar_listings = bazaar_data.listings if bazaar_data else []
        all_listings = bazaar_listings + market_listings

        if not all_listings:
             await interaction.followup.send(f"'{official_name}' の出品が見つかりませんでした。", ephemeral=True)
             return

        # ソート
        all_listings.sort(key=lambda x: x.price)
        cheapest = all_listings[0]

        # Embed作成
        embed = Embed(title=f"Price Check: {official_name}", color=Color.green())
        embed.add_field(name="最安値", value=f"${cheapest.price:,}", inline=True)
        embed.add_field(name="数量", value=f"{cheapest.quantity:,}", inline=True)
        embed.add_field(name="ソース", value=cheapest.source, inline=True)

        # 上位5件を表示
        top_listings_str = ""
        for listing in all_listings[:5]:
             source_short = "Bazaar" if listing.source == "Bazaar" else "ItemMkt"
             top_listings_str += f"**${listing.price:,}** x{listing.quantity:,} ({source_short})\n"

        embed.add_field(name="上位の出品", value=top_listings_str, inline=False)
        embed.set_footer(text=f"Total Listings: {len(all_listings)}")

        await interaction.followup.send(embed=embed)

    @tree.command(name="notification_channel", description="通知を送信するチャンネルを設定します")
    @app_commands.describe(channel="通知先のチャンネル")
    async def notification_channel(interaction: Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        db.set_config("notification_channel_id", str(channel.id))
        await interaction.response.send_message(f"通知チャンネルを {channel.mention} に設定しました。")

    @tree.command(name="watch", description="アイテムの価格監視を設定します")
    @app_commands.describe(item_name="監視するアイテム名", price="この価格を下回ったら通知")
    async def watch(interaction: Interaction, item_name: str, price: int):
        await interaction.response.defer(ephemeral=True)
        loop = asyncio.get_running_loop()

        item_id = db.get_item_id(item_name)

        if not item_id:
             if api_key and api_key != "TORN_API_KEY":
                 items = await loop.run_in_executor(None, marketplace.fetch_all_items, api_key)
                 if items:
                     db.upsert_items(items)
                     item_id = db.get_item_id(item_name)

        if not item_id:
             await interaction.followup.send(f"アイテム '{item_name}' が見つかりませんでした。", ephemeral=True)
             return

        official_name = db.get_item_name(item_id)

        db.add_watch(item_id, price)

        await interaction.followup.send(f"'{official_name}' が ${price:,} を下回ったら通知します。")

    @tree.command(name="watchlist", description="監視中のアイテム一覧を表示します")
    async def watchlist(interaction: Interaction):
        watches = db.get_all_watches()

        if not watches:
            await interaction.response.send_message("現在監視中のアイテムはありません。", ephemeral=True)
            return

        embed = Embed(title="監視リスト", color=Color.blue())

        for item_id, threshold in watches:
            item_name = db.get_item_name(item_id) or f"Unknown Item (ID: {item_id})"
            embed.add_field(name=item_name, value=f"${threshold:,}")
        
        await interaction.response.send_message(embed=embed)
