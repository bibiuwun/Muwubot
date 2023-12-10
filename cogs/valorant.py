import discord
from discord.ext import commands
import json
import datetime
import asyncio
from easy_pil import Editor, load_image_async, Font, Canvas
import io
import random
from discord import app_commands


class Valorant(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.command()  #
  async def valcard(self, ctx, member: discord.Member = None):
    if member == None:
      await ctx.send("<!valcard @user>")
      return
    users = get_cards_data()
    name = member.display_name
    pfp = member.display_avatar
    player = users[str(member.id)]["Player"]
    skin = users[str(member.id)]["Favorite Skin"]
    role = users[str(member.id)]["Main Role"]
    rank = users[str(member.id)]["Rank"]
    social = users[str(member.id)]["Social Link"]
    em = discord.Embed(title=f"{player}",
                       description=f"My favorite skin is {skin} :)",
                       color=0xfff00)
    em.set_author(
        name=f"{name}",
        icon_url=
        "https://yoolk.ninja/wp-content/uploads/2020/06/Games-Valorant-1024x1024.png"
    )
    em.set_thumbnail(url=f"{pfp}")
    em.add_field(name=f"{rank} {role}", value=f"Me: {social}", inline=False)
    await ctx.send(embed=em)
    
  ##### /valorantcard (parameters) #####
  @app_commands.command(name="valorantcard")
  @app_commands.describe(
      name="name/alias",
      player="ign#tag",
      role="Controller, Duelist, Initiator, Sentinel, Fill",
      rank=
      "Iron, Bronze, Silver, Gold, Platinum, Diamond, Ascendant, Immortal, Radiant",
      social='@tag/link',
      bestskin='your own skin-gun combo')
  async def valorantcard(self, interaction: discord.Interaction, name: str,
                         player: str, role: str, rank: str, social: str,
                         bestskin: str):
    await interaction.response.send_message(
        f"Use **<!valcard @user>**, Valorant player card created for {interaction.user.mention}."
    )
    user = interaction.user
    new_card(user)
    users = get_cards_data()
    users[str(user.id)]["Name"] = name
    users[str(user.id)]["Player"] = player
    users[str(user.id)]["Main Role"] = role
    users[str(user.id)]["Rank"] = rank
    users[str(user.id)]["Social Link"] = social
    users[str(user.id)]["Favorite Skin"] = bestskin
    with open("./uwuplayercharts.json", "w") as f:
      json.dump(users, f)


async def setup(bot):
  await bot.add_cog(Valorant(bot))

def get_cards_data():
  with open("./uwuplayercharts.json", "r") as f:
    users = json.load(f)
  return users

def new_card(user):
  users = get_cards_data()
  if str(user.id) in users:
    return False
  else:
    users[str(user.id)] = {}
    users[str(user.id)]["Name"] = ''
    users[str(user.id)]["Player"] = ''
    users[str(user.id)]["Main Role"] = ''
    users[str(user.id)]["Rank"] = ''
    users[str(user.id)]["Social Link"] = ''
    users[str(user.id)]["Favorite Skin"] = ''
  with open("uwuplayercharts.json", "w") as f:
    json.dump(users, f)
  return True