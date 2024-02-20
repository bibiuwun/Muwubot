import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
import io
import random 
import sqlite3

#test-general
#SERVER_CHANNEL_ID = 1179238207066488885

class Gamble(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command()
  @commands.cooldown(1, 60, commands.BucketType.user) #1 every 1 min (in secs)
  async def beg(self, ctx):
    player = ctx.author
    await add_player(player) # Correct function name here
    player_data = await get_player_data()
    earnings = random.randrange(101)
    if str(player.id) in player_data:
      player_nuggies = player_data[str(player.id)]
      new_balance = player_nuggies + earnings
      await update_player_balance(player, new_balance)
      await ctx.reply(f"Recieved {earnings} nuggies!! Total nuggies: {new_balance}.")
    else:
      await ctx.reply("Error: Account not found.")   
  @beg.error
  async def beg_error(self, ctx, error):
      if isinstance(error, commands.CommandOnCooldown):
          await ctx.reply(f"Cooldown. Use again in {error.retry_after:.2f}s.")
      else:
          raise error
        
  @commands.command(aliases=["nuggies", "nugs"])
  async def check_nuggies(self, ctx, player: discord.Member = None):
    if player is None:
        player = ctx.author
    player_id_str = str(player.id)
    player_data = await get_player_data()
    if player_id_str in player_data:
      nuggies_amount = player_data[player_id_str]
      await ctx.reply(f"{player.display_name} has {nuggies_amount} nuggies!")
    else:
      await ctx.reply(f"{player.display_name} does not have an account yet. Type `!beg` to get started!")

  @commands.command(aliases=["lb", "leaderboard"])
  async def nuggieboard(self, ctx): #limit 5
    conn = sqlite3.connect('nuggies.db')
    c = conn.cursor()
    c.execute('SELECT user_id, nuggies FROM players ORDER BY nuggies DESC LIMIT 5') 
    top_players = c.fetchall()
    conn.close()

    if top_players:
      em = discord.Embed(title="Nuggie Leaderboard")
      for count, (user_id, nuggies) in enumerate(top_players, start=1):
        user = await self.bot.fetch_user(int(user_id))
        em.add_field(name=f"{count}. {user.display_name}", value=f"Nuggies: **{nuggies}**", inline=False)
      await ctx.reply(embed=em)
    else:
      await ctx.reply("No Data Found.")
      
############ gamble function      
  @commands.command()
  @commands.cooldown(1, 5, commands.BucketType.user)  #once every 5 sec
  async def gamble(self, ctx, amount: str, percent: int = 60):
      player = ctx.author
      players = await get_player_data()  
      amount = int(amount)  # Convert amount to integer
      if int(amount) <= 0 or int(amount) > players[str(player.id)]:
        await ctx.reply("You don't have enough nuggies.")
        return

      dice = random.randrange(2) #50-50
      if dice == 1:  # Win
        new_balance = players[str(player.id)] + amount
        await update_player_balance(player, new_balance)
        await ctx.reply(
            f"You won the gamble! You won {amount} nuggies and now have {new_balance} nuggies."
        )
      else:  # Lose
        new_balance = players[str(player.id)] - amount
        await update_player_balance(player, new_balance)
        await ctx.reply(
            f"You lost the gamble. You lost {amount} nuggies and now have {new_balance} nuggies."
        )
######### gamble funciton
async def setup(bot):
  await bot.add_cog(Gamble(bot))

###########################
## DB HELPER FUNCTIONS
async def add_player(user, nuggies=0):
  conn = sqlite3.connect('nuggies.db')
  c = conn.cursor()
  c.execute('''
    CREATE TABLE IF NOT EXISTS players (
      user_id TEXT PRIMARY KEY,
      nuggies INTEGER
    )
  ''')
  c.execute('''
    INSERT INTO players (user_id, nuggies) 
    VALUES (?, ?)
    ON CONFLICT(user_id) 
    DO NOTHING
  ''', (str(user.id), nuggies))
  conn.commit()
  conn.close()

async def get_player_data():
  conn = sqlite3.connect('nuggies.db')
  c = conn.cursor()
  c.execute('SELECT * FROM players') 
  players = {row[0]: row[1] for row in c.fetchall()}
  conn.close()
  return players
  
async def update_player_balance(user, new_balance):
  conn = sqlite3.connect('nuggies.db')
  c = conn.cursor()
  c.execute('''
    UPDATE players
    SET nuggies = ?
    WHERE user_id = ?
  ''', (new_balance, str(user.id)))
  conn.commit()
  conn.close()

