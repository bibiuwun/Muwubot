import discord
from discord.ext import commands
import json
import datetime
import asyncio
from easy_pil import Editor, load_image_async, Font, Canvas
import io
import random


class Leveling(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command()
  async def level(self, ctx, member: discord.Member = None):
    """
      !level -> Shows your leveling information
      !level @User -> Shows the leveling information of the mentioned user
    """
    if member == None:
      member = ctx.author
      
    users = get_levels_data()
    user_data = {
        "name": f"{member.name}",
        "xp": users[str(member.id)]['xp'],
        "level": users[str(member.id)]['level'],
        "next_level_xp": 1000,
        "percentage": users[str(member.id)]['xp']}
    await levelbanner(ctx, member, user_data)

  @commands.command(aliases=["lvlb", "lvlboard", "levelleader", "lvlleader"])
  async def levelboard(self, context):
    """
      !levelboard -> Shows the levels leader boards 
      !lvlb, !lvlboard, !levelleader, !lvlleader  
    """
    d = get_levels_data()  
    data = sorted(d.items(),
                  key=lambda x: (x[1]['level'], x[1]['xp']),
                  reverse=True)[:5] #top 5 users
    if data:
      em = discord.Embed(title="Level Leaderboard")
      for count, (user_id, user_info) in enumerate(data, start=1):
        user = await self.bot.fetch_user(int(user_id))
        em.add_field(
            name=f"{count}.{user.name}",
            value=f"Level: **{user_info['level']}** | XP: **{user_info['xp']}**",
            inline=False)
      return await context.send(embed=em)
    return await context.send("No Data Found")
    
      
  @commands.Cog.listener() #@bot.event
  async def on_message(self, message):
    user = message.author
    if user.bot:
      return  #no xp for muwu

    new_person(user)
    users = get_levels_data()
    dice = random.randrange(9)
    update_xp_data(user, dice)

    if users[str(user.id)]['xp'] >= 1000:
      levelup(user)
      await message.channel.send(f"{user.mention} has reached **Level {users[str(user.id)]['level']+1}**!!")
      user_data = {
        "name": f"{user.name}",
        "xp": users[str(user.id)]['xp'] - 1000,
        "level": users[str(user.id)]['level'] + 1,
        "next_level_xp": 1000,
        "percentage": users[str(user.id)]['xp'] - 1000}
      await levelbanner(message.channel, user, user_data)


async def setup(bot):
  await bot.add_cog(Leveling(bot)) ##add_cog 

async def levelbanner(text, member, user_data):
  background = Editor("./imgs/levelup.png")
  profile_picture = await load_image_async(str(member.avatar.url))
  profile = Editor(profile_picture).resize((150, 150)).circle_image()
  poppins = Font.poppins(size=38)
  poppins_small = Font.poppins(size=30)
  background.paste(profile, (30, 30))
  background.ellipse((30, 30), 150, 150, outline="#e0c3a4", stroke_width=2)
  #fill_width = (user_data["percentage"] / 100) * 800
  background.bar((30, 220),
                 max_width=800,
                 height=30,
                 percentage=100,
                 color="#c7b7bb",
                 radius=40)
  background.bar((30, 220),
                 max_width=800,
                 height=30,
                 percentage=user_data["percentage"] / 10,
                 color="#282828",
                 radius=30)
  background.text((200, 50), user_data["name"], font=poppins, color="#FFFFFF")
  background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
  background.text(
      (200, 110),
      f"Level:  {user_data['level']} | XP: {user_data['xp']}/{user_data['next_level_xp']}",
      font=poppins_small,
      color="#FFFFFF")
  with io.BytesIO() as image_binary:
    background.image.save(image_binary, format="PNG")
    image_binary.seek(0)
    file = discord.File(fp=image_binary, filename="levelcard.png")
    await text.send(file=file)

def levelup(user):
  users = get_levels_data()
  if str(user.id) in users:
    users[str(user.id)]["level"] += 1
    users[str(user.id)]["xp"] = 0
    with open("./uwulevels.json", "w") as f:
      json.dump(users, f)
  else:
    return False
  return True

def update_levels_data(user):
  users = get_levels_data()
  if str(user.id) in users:
    users[str(user.id)]["level"] += 1
    with open("./uwulevels.json", "w") as f:
      json.dump(users, f)
  else:
    return False
  return True

def update_xp_data(user, num):
  users = get_levels_data()
  if str(user.id) in users:
    users[str(user.id)]["xp"] += num
    with open("./uwulevels.json", "w") as f:
      json.dump(users, f)
  else:
    return False
  return True

def new_person(user):
  users = get_levels_data()
  if str(user.id) in users:
    return False
  else:
    users[str(user.id)] = {}
    users[str(user.id)]["level"] = 0
    users[str(user.id)]["xp"] = 0
  with open("./uwulevels.json", "w") as f:
    json.dump(users, f)
  return True

def get_levels_data():
  with open("./uwulevels.json", "r") as f:
    users = json.load(f)
  return users
