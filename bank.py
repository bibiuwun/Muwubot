import discord
from discord.ext import commands
import json
import datetime
import asyncio
from easy_pil import Editor, load_image_async, Font, Canvas
import io
import random


#WWIIIIPPPP
class Mesosbank(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command(aliases=["m"])
  async def mesos(self, ctx, player: discord.Member = None):
    """
      !mesos, !m -> Shows your mesos infomation
      !mesos @User -> Shows the mesos information of the mentioned user
    """
    if player == None:
      player = ctx.author
    new_player(player)
    players = get_bank_data()
    points_amt = players[str(player.id)]["mesos"]
    em = discord.Embed(title=f"{player.name} has {points_amt} mesos",
                       color=discord.Color.random())
    await ctx.send(embed=em)

  @commands.command(aliases=["mb", "mesosb", "gambleboard", "gambleb", "mesosleader"])
  async def mesosboard(self, ctx):
    """
      !mesosboard -> Shows the levels leader boards 
      !mb, !mesosb, !gambleboard, !gambleb, !mesosleader
    """
    d = get_bank_data()  #user top 5
    data = sorted(d.items(), key=lambda x: (x[1]['mesos']), reverse=True)[:5]
    if data:
      em = discord.Embed(title="Mesos Leaderboard")
      for count, (user_id, user_info) in enumerate(data, start=1):
        user = await self.bot.fetch_user(int(user_id))
        em.add_field(name=f"{count}.{user.name}",
                     value=f"Mesos: **{user_info['mesos']}**",
                     inline=False)
      return await ctx.send(embed=em)
    return await ctx.send("No Data Found")
    
  @commands.command()
  @commands.cooldown(1, 86400, commands.BucketType.user)  #once every 24h
  async def daily(self, ctx):
    """
      !daily -> Provides a daily mesos sum
    """
    player = ctx.author
    new_player(player)
    players = get_bank_data()
    earnings = 5000 #change later to the amount of begs you can do in a day
    players[str(player.id)]["mesos"] += earnings
    with open("uwubank.json", "w") as f:
      json.dump(players, f)
    update_players = get_bank_data()
    await ctx.reply(f"Recieved {earnings} mesos!! Total mesos: {update_players[str(player.id)]['mesos']}.")
    
  @commands.command()
  @commands.cooldown(2, 600, commands.BucketType.user) #2 times every 10 min (in secs)
  async def beg(self, ctx):
    """
      !beg -> Provides a random amount of mesos
    """
    player = ctx.author
    new_player(player)
    players = get_bank_data()
    earnings = random.randrange(101)
    players[str(player.id)]["mesos"] += earnings
    with open("uwubank.json", "w") as f:
      json.dump(players, f)
    update_players = get_bank_data()
    await ctx.send(f"Recieved {earnings} mesos!! Total mesos: {update_players[str(player.id)]['mesos']}.")

  # Give command, written by Andrew
  @commands.command()
  @commands.cooldown(1, 5, commands.BucketType.user)  #once every 5 sec
  async def give(self, ctx, target: discord.Member == None, amount: int = None):
    """
      !give <@target_user> <mesos amount> -> Gives mesos to the target user
    """
    try:
      #print(target.id)
      player = ctx.author
      players = get_bank_data()
      if amount < 0:
        await ctx.reply(embed=discord.Embed(
            title="Error",
            description=f":x: I see you trying to steal mesos >:(",
            color=0xff1100))
        return
      if player == target:
        await ctx.reply(embed=discord.Embed(
            title="Error",
            description=f":x: You can't give yourself mesos!",
            color=0xff1100))
        return
      if str(target.id) not in players.keys():
        await ctx.reply(embed=discord.Embed(
            title="Error",
            description=f":x: Target person didn't initialize mesos!",
            color=0xff1100))
        return
      if amount > players[str(player.id)]["mesos"]:
        await ctx.reply(
            embed=discord.Embed(title="Error",
                                description=f":x: You don't have enough mesos!",
                                color=0xff1100))
        return ##take away initial bet
      players[str(player.id)]["mesos"] -= amount
      players[str(target.id)]["mesos"] += amount
      await ctx.reply(embed=discord.Embed(
          description=
          f"Gave {amount} mesos to {target.global_name}! You now have **{players[str(player.id)]['mesos']}** mesos."
      ))
      with open("./uwubank.json", "w") as f:
        json.dump(players, f)
    except:
      await ctx.reply(
          "You and/or your recipient have no mesos, start with !daily, !beg, or !mesos to initialize."
      )
      
  @commands.command()
  @commands.cooldown(1, 5, commands.BucketType.user)  #once every 5 sec
  async def gamble(self, ctx, amount: str, percent: int = 60):
    """
      !gamble <all or mesos> <optional: 30 or 60> -> User gambles their mesos
    """
    player = ctx.author
    players = get_bank_data()  
    if amount.lower() == 'all':
      amount = players[str(player.id)]["mesos"]
    else:
      try:
          amount = int(amount)  # Convert amount to integer
      except ValueError:
          await ctx.reply("Please enter a valid amount of mesos.")
          return
        
    if int(amount) <= 0 or int(amount) > players[str(player.id)]["mesos"]:
      await ctx.reply("You don't have enough mesos.")
      return
    if percent not in (30, 60):
      await ctx.reply("Enter <30 or 60> only.")
      return
    dice = random.randrange(101)
    if (amount == 'all') or (percent == 60):
      current = players[str(player.id)]["mesos"]
      winnings = int(amount) * 2
      if dice > 40:  #60% scrolling
        players[str(player.id)]["mesos"] -= int(amount) ##
        players[str(player.id)]["mesos"] += winnings
        await ctx.reply(
            f"{player}'s Current: {current}\nYour winnings: {amount}*2 = {winnings}\nYour 60% scroll **passed**. You have {players[str(player.id)]['mesos']} mesos!!"
        )
      elif dice <= 40:  #60% scrolling
        difference = players[str(player.id)]["mesos"] - int(amount)
        if difference <= 0:
          players[str(player.id)]["mesos"] = 0
        else:
          players[str(player.id)]["mesos"] -= int(amount)
        await ctx.reply(
            f"{player}'s Current: {current}\nYour losses: {amount}\nYour 60% scroll **failed**. You have {players[str(player.id)]['mesos']} mesos!!"
        )
      with open("./uwubank.json", "w") as f:
        json.dump(players, f)
    elif percent == 30:
      current = players[str(player.id)]["mesos"]
      winnings = int(amount) * 5
      losses = int(amount) * 2
      if dice > 70:  #30% scrolling
        players[str(player.id)]["mesos"] -= current ##
        players[str(player.id)]["mesos"] += winnings
        await ctx.reply(
            f"{player}'s Current: {current}\nYour winnings: {amount}*5 = {winnings}\nYour 30% scroll **passed**. You have {players[str(player.id)]['mesos']} mesos!!"
        )
      elif dice <= 70:  #30% scrolling
        difference = players[str(player.id)]["mesos"] - int(amount) * 2
        if difference <= 0:
          players[str(player.id)]["mesos"] = 0
        else:
          players[str(player.id)]["mesos"] -= int(amount) * 2
        await ctx.reply(
            f"{player}'s Current: {current}\nYour losses: {amount}*2 = -{losses}\nYour 30% scroll **failed**. You have {players[str(player.id)]['mesos']} mesos!!"
        )
      with open("./uwubank.json", "w") as f:
        json.dump(players, f)
      #print('test')
    else:
      await ctx.reply(
          "No mesos, start with !daily, !beg, or !mesos to initialize.")

  #@commands.command()
  #@commands.Cog.listener('on_command_error')
  #async def on_command_error(self, ctx, error):
  #    elif ctx.command.name == 'daily': 
  #      message = f"You nooob addict! Cooldown for daily: {int(error.retry_after // 3600)}h {(int(error.retry_after) % 3600) // 60}m."
  #      await ctx.send(message)
  #    elif ctx.command.name == 'beg': 
  #      message = f"You nooob addict! Cooldown for beg: {(int(error.retry_after) % 3600) // 60}m."
  #      await ctx.send(message)
  #  else:
  #      pass #add general error message later
      
async def setup(bot):
  await bot.add_cog(Mesosbank(bot)) ##add_cog 

def new_player(player):
  players = get_bank_data()
  if str(player.id) in players:
    return False
  else:
    players[str(player.id)] = {}
    players[str(player.id)]["mesos"] = 0
  with open("./uwubank.json", "w") as f:
    json.dump(players, f)

def get_bank_data():
  with open("./uwubank.json", "r") as f:
    players = json.load(f)
  return players
