import discord, random, os
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

# connect to MongoDB cluster
load_dotenv()
CLIENT = MongoClient(os.environ["MONGODB_URI"])

# initialize db collection
DB = CLIENT["muwu_data"]
BALANCES = DB["balances"]
SERVERS = DB["servers"]

CURRENCY = "nuggies"

class Gamble(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command()
  @commands.cooldown(1, 30, commands.BucketType.user) # once every 30 sec
  async def beg(self, ctx):
    player = ctx.author
    earnings = random.randrange(1,101)
    player_balance = _update_player_balance(player.id, earnings)
    await ctx.reply(embed=discord.Embed(
      description=f"🪙 Received `{earnings}` {CURRENCY}!! You now have `{player_balance}` {CURRENCY}.",
      color=discord.Color.brand_green()
      ))
  @beg.error
  async def beg_error(self, ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
      await ctx.reply(embed=discord.Embed(
        description=f"⏳ On cooldown. Try again in {error.retry_after:.2f}s.",
        color=discord.Color.gold()
        ))
    else:
      await ctx.reply(f"{error}")
      raise error

  @commands.command(aliases=["nuggies", "nugs", "balance", "bal"])
  async def check_balance(self, ctx, player: discord.Member = None):
    if player is None:
        player = ctx.author
    player_balance = _get_player_balance(player.id)
    if player_balance == 0:
      await ctx.reply(embed=discord.Embed(
        description=f"⚠️ {player.display_name} has no {CURRENCY}! Type `!beg` to get started!",
        color=discord.Color.gold()
      ))
    else:
      await ctx.reply(embed=discord.Embed(
        description=f"💰 {player.display_name} has `{player_balance}` {CURRENCY}!",
        color=discord.Color.brand_green()
      ))

  # TODO: design data model and rework helper function to display only server members
  @commands.command(aliases=["lb", "nuggieboard"])
  async def leaderboard(self, ctx): # limit 5
    #server_id = ctx.guild.id
    leaderboard = _get_global_leaderboard()
    #leaderboard = _get_server_leaderboard(server_id)
    
    embed=discord.Embed(
      title=f"Total {CURRENCY.capitalize()} Leaderboard",
      description=f"Top 5 players",
      color=discord.Color.random()
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
      embed.add_field(name=f"**{count}. {username}**", value=f"> {balance} {CURRENCY.lower()}", inline=False)
    await ctx.reply(embed=embed)

  @commands.command()
  @commands.cooldown(1, 2.5, commands.BucketType.user)  # once every 2.5 sec
  async def gamble(self, ctx, amount: int | str, percent: int = 60):
    player = ctx.author
    player_balance = _get_player_balance(player.id)
    
    if isinstance(amount, str):
      if amount.lower() == "all":
        amount = player_balance
      else:
        await ctx.reply(embed=discord.Embed(
          description="⚠️ Invalid amount.",
          color=discord.Color.gold()
          ))
        return
    elif isinstance(amount, int):
      if amount <= 0:
        await ctx.reply(embed=discord.Embed(
          description="⚠️ Invalid amount.",
          color=discord.Color.gold()
          ))
        return
      
    if player_balance <= 0 or amount > player_balance:
      await ctx.reply(embed=discord.Embed(
        description="⚠️ You don't have enough {CURRENCY}.",
        color=discord.Color.gold()
        ))
      return
    dice = random.randrange(2) # 50-50
    if dice == 1: # win
      new_balance = _update_player_balance(player.id, amount)
      await ctx.reply(embed=discord.Embed(
        description=f"💸 You win `{amount}` {CURRENCY}! You now have `{new_balance}` {CURRENCY}.",
        color=discord.Color.brand_green()
        ))
    else: # lose
      new_balance = _update_player_balance(player.id, -amount)
      await ctx.reply(embed=discord.Embed(
        description=f"💢 You lose `{amount}` {CURRENCY}! You now have `{new_balance}` {CURRENCY}.",
        color=discord.Color.brand_red()
        ))
  @gamble.error
  async def gamble_error(self, ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
      await ctx.reply(embed=discord.Embed(
        description=f"⏳ On cooldown. Try again in {error.retry_after:.2f}s.",
        color=discord.Color.gold()
        ))
    else:
        await ctx.reply(f"{error}")
        raise error
    
  @commands.command()
  async def give(self, ctx, amount: int | str, target: discord.Member):
    player = ctx.author
    if target == ctx.author:
      await ctx.reply(embed=discord.Embed(
        description=f"⚠️ You can't give yourself {CURRENCY}!",
        color=discord.Color.gold()
        ))
      return
    
    player_balance = _get_player_balance(player.id)
    
    if isinstance(amount, str):
      if amount.lower() == "all":
        amount = player_balance
      else:
        await ctx.reply(embed=discord.Embed(
          description="⚠️ Invalid amount.",
          color=discord.Color.gold()
          ))
        return
    elif isinstance(amount, int):
      if amount <= 0:
        await ctx.reply(embed=discord.Embed(
          description="⚠️ Invalid amount.",
          color=discord.Color.gold()
          ))
        return

    if player_balance <= 0 or amount > player_balance:
      await ctx.reply(embed=discord.Embed(
        description="⚠️ You don't have enough {CURRENCY}.",
        color=discord.Color.gold()
        ))
      return
    
    new_player_balance = _update_player_balance(player.id, -amount)
    _update_player_balance(target.id, amount)
    
    await ctx.reply(embed=discord.Embed(
      description=f"📩 Gave `{amount}` {CURRENCY} to {target.display_name}! You now have `{new_player_balance}` {CURRENCY}."
    ))
  
  # TODO: daily/weekly lottery system

###########################

async def setup(bot):
  await bot.add_cog(Gamble(bot))

###########################
# MONGODB HELPER FUNCTIONS
def _get_player_balance(user_id: int) -> int: # return player's balance, create document if no player exists in db
  query = BALANCES.find_one_and_update(
    {"user_id": user_id},
    {"$setOnInsert": {"balance": 0}},
    upsert=True,
    return_document=ReturnDocument.AFTER
  )
  return query["balance"]

def _update_player_balance(user_id: int, earnings: int) -> int: # increment player's balance by earnings and return it, create document if no player exists in db
  query = BALANCES.find_one_and_update(
    {"user_id": user_id},
    {"$inc": {"balance": earnings}},
    upsert=True,
    return_document=ReturnDocument.AFTER
  )
  return query["balance"]

# remove once server leaderboard is ready
def _get_global_leaderboard() -> list[(int, int)]:
  cursor = BALANCES.find().sort("balance", -1).limit(5)
  output = []
  for document in cursor:
    output.append((document["user_id"], document["balance"]))
  cursor.close()
  return output

# TODO: finish below functions
#def _get_server_info(server_id: int):
#  query = SERVERS.find_one_and_update(
#    {"_id": server_id},
#    {"$setOnInsert": server_id},
#    upsert=True,
#    return_document=ReturnDocument.AFTER
#  )
#
#def _get_server_leaderboard(server_id: int) -> list[(int, int)]:
#  query = SERVERS.find_one_and_update(
#    {"server_id": server_id},
#    {"$setOnInsert": server_id},
#    upsert=True,
#    return_document=ReturnDocument.AFTER
#  )