### pip install discord
### pip install easy-pil
from discord.app_commands.errors import CommandOnCooldown
import config
import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
from discord import File
import json
import random
from discord import app_commands
import io
import dict
from pytz import timezone
import pytz
import os
from cogs.level import Leveling
from cogs.general import General
from cogs.general import hydration_message
from cogs.valorant import Valorant
from datetime import datetime


### INITIAL DELCARE
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event 
async def on_ready():
  await bot.load_extension("cogs.level")
  await bot.load_extension("cogs.bank")
  await bot.load_extension("cogs.general")
  await bot.load_extension("cogs.valorant")
  await bot.change_presence(activity=discord.Game("uwucodingg"))
  await bot.tree.sync()
  bot.loop.create_task(hydration_message(bot, "hydration, hydration, hydration!!", 1)) #currently set to 1 hour
  print("MuwuBot is Online")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        message = f"Cooldown: {round(error.retry_after, 1)} seconds."
        await ctx.reply(message)
    elif isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("You do not have the required permissions to use this command.")
    else:
        await ctx.reply("An unexpected error has occurred.")

@bot.event
async def on_error(event_method, *args, **kwargs):
    print(f"An error occurred: {event_method}")

########################################################### BIO/STATUS SYSTEM (TODO: move to file)
class StatusModal(discord.ui.Modal):

  def __init__(self):
    super().__init__(title="Status Changer")
    self.emStatus = discord.ui.TextInput(
        label="Status",
        min_length=1,
        max_length=40,
        required=True,
        placeholder="short status description",
        style=discord.TextStyle.short)
    self.add_item(self.emStatus)
    self.emBio = discord.ui.TextInput(label="Description",
                                      min_length=1,
                                      max_length=45,
                                      required=True,
                                      placeholder="short about me",
                                      style=discord.TextStyle.short)
    self.add_item(self.emBio)

  async def on_submit(self, interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Updated Status for {interaction.user.mention}", ephemeral=True)
    status = self.emStatus.value
    bio = self.emBio.value
    #timestamp = interaction.created_at
    date = datetime.now()
    current_date = date.astimezone(timezone('US/Pacific'))
    date_format = '%m/%d/%Y %H:%M:%S %Z'
    timestamp_str = current_date.strftime(date_format)
    print(timestamp_str)
    await add_status(interaction.user.mention, status, bio,
                            timestamp_str)
    #print(timestamp)


@bot.tree.command(name="update_status", description="update your bio and status")
async def update_status(interaction: discord.Interaction):
  await interaction.response.send_modal(StatusModal())


@bot.command(aliases=["cs", "ckstatus", "gs", "checkstatus", "getstatus"])
async def status(context, member: discord.Member = None):
  if member == None:
    await context.send("<!status @user>")
    return
  users = await get_status_data()
  #user = context.author
  name = member.display_name
  #print(member.id)
  #pfp = member.display_avatar
  user_data = {
      "name": f"{name}",
      "Status": users[str(member.id)]["Status"],
      "Bio": users[str(member.id)]["Bio"],
      "Timestamp": users[str(member.id)]["Timestamp"]
  }
  #em = discord.Embed(title=f"{status}",
  #                   description=f"{bio}",
  #                   color=discord.Color.random())
  #await context.send(embed=em)
  await statusbanner(context, member, user_data)

async def statusbanner(text, member, user_data):
  background = Editor("./imgs/sanrio1.png")
  profile_picture = await load_image_async(str(member.display_avatar.url))
  profile = Editor(profile_picture).resize((150, 150)).circle_image()
  poppins = Font.poppins(size=38)
  poppins_small = Font.poppins(size=30)
  background.paste(profile, (30, 30))
  background.ellipse((30, 30), 150, 150, outline="#e0c3a4", stroke_width=2)
  background.text((200, 50), user_data["name"], font=poppins, color="#FFFFFF")
  background.text((200, 125),
                  f"Status: {user_data['Status']}",
                  font=poppins_small,
                  color="#FFFFFF")
  background.text((200, 175),
                  f"Bio: {user_data['Bio']}",
                  font=poppins_small,
                  color="#FFFFFF")
  background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
  background.text((200, 235),
                  f"Last Modified: {user_data['Timestamp']}",
                  font=Font.poppins(size=25),
                  color="#FFFFFF")
  with io.BytesIO() as image_binary:
    background.image.save(image_binary, format="PNG")
    image_binary.seek(0)
    file = discord.File(fp=image_binary, filename="sanrio1.png")
    await text.send(file=file)

### STATUS CARD HELPER FUNCTION
async def add_status(user, status='', bio='', timestamp=''):
  user = user[2:-1]
  users = await get_status_data()
  if user in users:
    users[str(user)]["Status"] = status
    users[str(user)]["Bio"] = bio
    users[str(user)]["Timestamp"] = timestamp
  else:
    users[str(user)] = {}
    users[str(user)]["Status"] = status
    users[str(user)]["Bio"] = bio
    users[str(user)]["Timestamp"] = timestamp
  with open("uwustatus.json", "w") as f:
    json.dump(users, f)
  return True


### STATUS CARD HELPER FUNCTION
async def get_status_data():
  with open("uwustatus.json", "r") as f:
    users = json.load(f)
  return users
########################################################### BIO/STATUS SYSTEM (TODO: move to file)

#### RUN ####
if __name__ == "__main__":
  bot.run(config.TOKEN)

