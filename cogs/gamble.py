import discord, io, random, os
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

# connect to MongoDB cluster
load_dotenv()
client = MongoClient(os.environ["MONGODB_URI"])

# initialize db collection
db = client["muwu_data"]
balances = db["balances"]

#test-general
#SERVER_CHANNEL_ID = 1179238207066488885

class Gamble(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  # TODO: embed replies
  @commands.command()
  @commands.cooldown(1, 60, commands.BucketType.user) # once every minute
  async def beg(self, ctx):
    player = ctx.author
    earnings = random.randrange(1,101)
    player_balance = update_player_balance(player, earnings)
    await ctx.reply(f"Received {earnings} nuggies!! You now have {player_balance} nuggies.")
  @beg.error
  async def beg_error(self, ctx, error):
      if isinstance(error, commands.CommandOnCooldown):
          await ctx.reply(f"On cooldown. Try again in {error.retry_after:.2f}s.")
      else:
          await ctx.reply(f"{error}")
          raise error
        
  # TODO: embed replies
  @commands.command(aliases=["nuggies", "nugs", "balance", "bal"])
  async def check_nuggies(self, ctx, player: discord.Member = None):
    if player is None:
        player = ctx.author
    player_balance = get_player_balance(player)
    if player_balance == 0:
      await ctx.reply(f"{player.display_name} has no nuggies! Type `!beg` to get started!")
    else:
      await ctx.reply(f"{player.display_name} has {player_balance} nuggies!")

  # TODO: rework for MongoDB
  @commands.command(aliases=["lb", "nuggieboard"])
  async def leaderboard(self, ctx): # limit 5
    pass
  
    #conn = sqlite3.connect('nuggies.db')
    #c = conn.cursor()
    #c.execute('SELECT user_id, nuggies FROM players ORDER BY nuggies DESC LIMIT 5') 
    #top_players = c.fetchall()
    #conn.close()
#
    #if top_players:
    #  em = discord.Embed(title="Nuggie Leaderboard")
    #  for count, (user_id, nuggies) in enumerate(top_players, start=1):
    #    user = await self.bot.fetch_user(int(user_id))
    #    em.add_field(name=f"{count}. {user.display_name}", value=f"Nuggies: **{nuggies}**", inline=False)
    #  await ctx.reply(embed=em)
    #else:
    #  await ctx.reply("No Data Found.")
      
  # TODO: embed replies
  @commands.command()
  @commands.cooldown(1, 5, commands.BucketType.user)  # once every 5 sec
  async def gamble(self, ctx, amount: int | str, percent: int = 60):
    player = ctx.author
    player_balance = get_player_balance(player)
    
    if isinstance(amount, str):
      if amount.lower() == "all":
        amount = player_balance
      else:
        await ctx.reply("Invalid amount.")
        return
    elif isinstance(amount, int):
      if amount <= 0:
        await ctx.reply("Invalid amount.")
        return
      
    if player_balance <= 0 or amount > player_balance:
          await ctx.reply("You don't have enough nuggies.")
          return
    dice = random.randrange(2) # 50-50
    if dice == 1: # win
      new_balance = update_player_balance(player, amount)
      await ctx.reply(f"You win {amount} nuggies! You now have {new_balance} nuggies.")
    else: # lose
      new_balance = update_player_balance(player, -amount)
      await ctx.reply(f"You lose {amount} nuggies! You now have {new_balance} nuggies.")

###########################

async def setup(bot):
  await bot.add_cog(Gamble(bot))

###########################
# MONGODB HELPER FUNCTIONS
def get_player_balance(user) -> int: # return player's balance, create document if no player exists in db
  query = balances.find_one_and_update(
    {"user_id": user.id},
    {"$setOnInsert": {"balance": 0}},
    upsert=True,
    return_document=ReturnDocument.AFTER
    )
  return query["balance"]

def update_player_balance(user, earnings) -> int: # increment player's balance by earnings and return it, create document if no player exists in db
  query = balances.find_one_and_update(
    {"user_id": user.id},
    {"$inc": {"balance": earnings}},
    upsert=True,
    return_document=ReturnDocument.AFTER
    )
  return query["balance"]
