import os
import random
import discord
from discord.ext import bridge, commands
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

# connect to MongoDB cluster
load_dotenv()
CLIENT = MongoClient(os.environ["MONGODB_URI"])

# initialize db collection
DB = CLIENT["muwu_data"]
BALANCES = DB["balances"]
SERVERS = DB["servers"]

# customization options
CURRENCY: str = "nuggies"
CURRENCY_SINGULAR: str = "nuggie"
MIN_BEG: int = 0
MAX_BEG: int = 150


class Gamble(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @bridge.bridge_command(description=f"Beg for some {CURRENCY}")
    @commands.cooldown(1, 30, commands.BucketType.user)  # once every 30 sec
    async def beg(self, ctx):
        player = ctx.author
        earnings = random.randrange(MIN_BEG, MAX_BEG + 1)
        if earnings == 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"<a:NOPERS:1219751360946372658> Nobody gave you {CURRENCY}. Better luck next time.",
                    color=discord.Color.brand_red(),
                )
            )
            return
        player_balance = _update_player_balance(player.id, earnings)
        await ctx.respond(
            embed=discord.Embed(
                description=f"🪙 Received `{earnings}` {CURRENCY}!! You now have `{player_balance}` {CURRENCY}.",
                color=discord.Color.brand_green(),
            )
        )

    @beg.error
    async def beg_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                embed=discord.Embed(
                    description=f"⏳ On cooldown. Try again in {error.retry_after:.2f}s.",
                    color=discord.Color.gold(),
                )
            )
        else:
            await ctx.respond(f"{error}")
            raise error

    @bridge.bridge_command(description=f"Get your balance in {CURRENCY}")
    async def balance(self, ctx, player: discord.Member = None):
        if player is None:
            player = ctx.author
        player_balance = _get_player_balance(player.id)
        if player_balance == 0:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"⚠️ {player.display_name} has no {CURRENCY}! Type `!beg` to get started!",
                    color=discord.Color.gold(),
                )
            )
        else:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"💰 {player.display_name} has `{player_balance}` {CURRENCY}!",
                    color=discord.Color.brand_green(),
                )
            )

    # TODO: design data model and rework helper function to display only server members
    @bridge.bridge_command(description=f"View the top 5 {CURRENCY_SINGULAR} balances")
    async def leaderboard(self, ctx):  # limit 5
        # server_id = ctx.guild.id
        leaderboard = _get_global_leaderboard()
        # leaderboard = _get_server_leaderboard(server_id)

        embed = discord.Embed(
            title=f"Total {CURRENCY.capitalize()} Leaderboard",
            description="Top 5 players",
            color=discord.Color.random(),
        )

        for count, (user_id, balance) in enumerate(leaderboard, start=1):
            user = await self.bot.fetch_user(user_id)
            username = user.display_name
            if count == 1:
                username += " 🥇"
            elif count == 2:
                username += " 🥈"
            elif count == 3:
                username += " 🥉"
            embed.add_field(
                name=f"**{count}. {username}**",
                value=f"> {balance} {CURRENCY.lower()}",
                inline=False,
            )
        await ctx.respond(embed=embed)

    @bridge.bridge_command(
        description=f"Gamble away your life savings of {CURRENCY_SINGULAR}"
    )
    @commands.cooldown(1, 2.5, commands.BucketType.user)  # once every 2.5 sec
    async def gamble(self, ctx, amount):
        player = ctx.author
        player_balance = _get_player_balance(player.id)

        if isinstance(amount, str):
            if amount.lower() == "all":
                amount = player_balance
            elif amount.isdigit():
                amount = int(amount)
            else:
                await ctx.respond(
                    embed=discord.Embed(
                        description="⚠️ Invalid amount.", color=discord.Color.gold()
                    )
                )
                return
        else:
            await ctx.respond(
                embed=discord.Embed(
                    description="⚠️ Invalid amount.", color=discord.Color.gold()
                )
            )
            return

        if player_balance <= 0 or amount > player_balance:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"⚠️ You don't have enough {CURRENCY}.",
                    color=discord.Color.gold(),
                )
            )
            return
        dice = random.randrange(2)  # 50-50
        if dice == 1:  # win
            new_balance = _update_player_balance(player.id, amount)
            await ctx.respond(
                embed=discord.Embed(
                    description=f"💸 You win `{amount}` {CURRENCY}! You now have `{new_balance}` {CURRENCY}.",
                    color=discord.Color.brand_green(),
                )
            )
        else:  # lose
            new_balance = _update_player_balance(player.id, -amount)
            await ctx.respond(
                embed=discord.Embed(
                    description=f"💢 You lose `{amount}` {CURRENCY}! You now have `{new_balance}` {CURRENCY}.",
                    color=discord.Color.brand_red(),
                )
            )

    @gamble.error
    async def gamble_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                embed=discord.Embed(
                    description=f"⏳ On cooldown. Try again in {error.retry_after:.2f}s.",
                    color=discord.Color.gold(),
                )
            )
        else:
            await ctx.respond(f"{error}")
            raise error

    @bridge.bridge_command(description=f"Give {CURRENCY} to another user")
    async def give(self, ctx, target: discord.Member, amount):
        player = ctx.author
        if target == ctx.author:
            await ctx.respond(
                embed=discord.Embed(
                    description=f"⚠️ You can't give yourself {CURRENCY}!",
                    color=discord.Color.gold(),
                )
            )
            return

        player_balance = _get_player_balance(player.id)

        if isinstance(amount, str):
            if amount.lower() == "all":
                amount = player_balance
            elif amount.isdigit():
                amount = int(amount)
            else:
                await ctx.respond(
                    embed=discord.Embed(
                        description="⚠️ Invalid amount.", color=discord.Color.gold()
                    )
                )
                return
        else:
            await ctx.respond(
                embed=discord.Embed(
                    description="⚠️ Invalid amount.", color=discord.Color.gold()
                )
            )
            return

        if player_balance <= 0 or amount > player_balance:
            await ctx.respond(
                embed=discord.Embed(
                    description="⚠️ You don't have enough {CURRENCY}.",
                    color=discord.Color.gold(),
                )
            )
            return

        new_player_balance = _update_player_balance(player.id, -amount)
        _update_player_balance(target.id, amount)

        await ctx.respond(
            embed=discord.Embed(
                description=f"📩 Gave `{amount}` {CURRENCY} to {target.display_name}! You now have `{new_player_balance}` {CURRENCY}."
            )
        )

    @give.error
    async def give_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.respond(
                embed=discord.Embed(
                    description=f"⚠️ Usage: !give <@user> <amount | all>",
                    color=discord.Color.gold(),
                )
            )
        else:
            await ctx.respond(f"{error}")
            raise error

    # TODO: daily raffle system
    # @commands.command()
    # async def raffle(self, ctx, action: str = None):
    #     player = ctx.author
    #     if action == None:
    #         # TODO: show raffle info, pot size, ending date/time, # of participants
    #         pass
    #     elif action.lower() == "join":
    #         # TODO: user joins raffle, increase pot size (with conditions)
    #         pass

    # TODO: weekly lottery system
    # @commands.command()
    # async def lottery(self, ctx, action: str = None):
    #    pass


###########################


def setup(bot):
    bot.add_cog(Gamble(bot))


###########################
# MONGODB HELPER FUNCTIONS


# return player's balance, create document if no player exists in db
def _get_player_balance(user_id: int) -> int:
    balance_query = BALANCES.find_one_and_update(
        {"_id": user_id},
        {"$setOnInsert": {"balance": 0}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return balance_query["balance"]


# increment player's balance by earnings and return it, create document if no player exists in db
def _update_player_balance(user_id: int, earnings: int) -> int:
    query = BALANCES.find_one_and_update(
        {"_id": user_id},
        {"$inc": {"balance": earnings}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return query["balance"]


# remove once server leaderboard is ready
def _get_global_leaderboard() -> list[(int, int)]:
    cursor = BALANCES.find().sort("balance", -1).limit(5)
    output = []
    for document in cursor:
        output.append((document["_id"], document["balance"]))
    cursor.close()
    return output


# TODO: finish below functions
# def _get_server_raffle(server: discord.Guild):
#    query = SERVERS.find_one(
#        {"_id": server.id},
#        {"$setOnInsert": {"raffle": {"ongoing": False}}},
#        upsert=True,
#        return_document=ReturnDocument.AFTER,
#    )

# def _get_server_leaderboard(server_id: int) -> list[(int, int)]:
#  query = SERVERS.find_one_and_update(
#    {"_id": server_id},
#    {"$setOnInsert": server_id},
#    upsert=True,
#    return_document=ReturnDocument.AFTER
#  )
