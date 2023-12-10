import discord
from discord.ext import commands
import datetime
import asyncio
from easy_pil import Editor, load_image_async, Font, Canvas
import io
import random
from discord import app_commands

SERVER_CHANNEL_ID = 1179238207066488885


class General(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot
  
  @commands.Cog.listener()
  async def on_member_join(self, member):
    channel = member.guild.system_channel
    if channel is None:
      return
    background = Editor("./imgs/whalecum.jpg")
    profile_image = await load_image_async(str(member.avatar.url))
    profile = Editor(profile_image).resize((150, 150)).circle_image()
    poppins = Font.poppins(size=50, variant="bold")
    background.paste(profile, (325, 90))
    background.ellipse((325, 90), 150, 150, outline="#e0c3a4", stroke_width=3)
    background.text((400, 260),
                    f"Whalecum {member.name}",
                    color="#e0c3a4",
                    font=poppins,
                    align="center")
    file = discord.File(fp=background.image_bytes, filename="whalecum.jpg")
    await channel.send(file=file)

  @commands.command()  #fkumuwu
  async def fkumuwu(self, ctx):
    background = Editor("imgs/fkumuwu.png")
    with io.BytesIO() as image_binary:
      background.image.save(image_binary, format="PNG")
      image_binary.seek(0)
      file = discord.File(fp=image_binary, filename="imgs/fkumuwu.png")
      await ctx.send(file=file)

  @app_commands.command(name="itempicker",
                    description="picks a random item from the listed")
  @app_commands.describe(items="enter items separated by commas")
  async def itempicker(self, interaction: discord.Interaction, items: str):
    item_list = [item.strip() for item in items.split(',')]
    em = discord.Embed(
        description=f"Gacha gods picked: **{random.choice(item_list)}**",
        color=0xad1457)
    await interaction.response.send_message(embed=em)
    

async def setup(bot):
  await bot.add_cog(General(bot))


### AUTOMATED HYDRATION HELPER FUNCTION
async def hydration_message(bot, msg, hour):
  while True:
    now = datetime.datetime.now()
    then = now + datetime.timedelta(hours=hour)
    wait_time = (then - now).total_seconds()
    await asyncio.sleep(wait_time)
    channel = bot.get_channel(SERVER_CHANNEL_ID)
    em = discord.Embed(title=f"{msg}", color=0x1abc9c)
    await channel.send(embed=em)
