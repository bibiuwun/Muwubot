import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas

#test-general
SERVER_CHANNEL_ID = 1179238207066488885

class Welcome(commands.Cog):
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

async def setup(bot):
  await bot.add_cog(Welcome(bot))