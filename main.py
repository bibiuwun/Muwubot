#module downloads; easy-pil, pytz
#standard library imports
#third party imports
import discord
from discord.ext import commands
#local application imports
import credentials
from cogs.welcome import Welcome
from cogs.statusmodal import StatusChangeModal, get_status_data, statusbanner
#import asyncpg

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
muwubot = commands.Bot(command_prefix="!", intents=intents)


@muwubot.event
async def on_ready():
  await muwubot.load_extension("cogs.welcome")
  await muwubot.load_extension("cogs.statusmodal")
  await muwubot.load_extension("cogs.gamble")
  print("MuwuBot is Online")


@muwubot.tree.command(name="update_status",
                      description="update your bio and status")
async def update_status(interaction: discord.Interaction):
  await interaction.response.send_modal(StatusChangeModal())

@muwubot.command(aliases=["checkstatus", "getstatus"])
async def status(context, member: discord.Member = None):
  if member is None:
    await context.reply("Use format: <!status @user>")
    return
  users = await get_status_data()
  user_id = str(member.id) #member.display_name
  if user_id in users:
      user_data = users[user_id]
      await statusbanner(context, member, user_data)
  else:
      await context.reply(f"The status for {member.mention} is not available.")



if __name__ == "__main__":
  #load personal credentials
  muwubot.run(credentials.TOKEN)
