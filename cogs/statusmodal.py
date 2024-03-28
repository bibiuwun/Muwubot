import os
import io
import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument
import sqlite3

# connect to MongoDB cluster
load_dotenv()
CLIENT = MongoClient(os.environ["MONGODB_URI"])

# initialize db collection
DB = CLIENT["muwu_data"]
USERS = DB["users"]


class StatusUpdateModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Set a status")
        self.emStatus = discord.ui.TextInput(
            label="Status",
            min_length=1,
            max_length=40,
            required=True,
            placeholder="What's poppin?",
            style=discord.TextStyle.short,
        )
        self.add_item(self.emStatus)

    async def on_submit(self, interaction: discord.Interaction):
        timePST = timezone("US/Pacific")
        timePSTnow = datetime.now(timePST)
        time_str = timePSTnow.strftime("%m/%d/%Y %H:%M:%S %Z")
        await _set_status(interaction.user.id, self.emStatus.value, time_str)
        await interaction.response.send_message(
            discord.Embed(
                description="Updated your status! Check your status with `!status`",
                color=discord.Color.random,
            ),
            ephemeral=True,
        )


class BioUpdateModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Set a user bio")
        self.emBio = discord.ui.TextInput(
            label="Description",
            min_length=1,
            max_length=45,
            required=True,
            placeholder="About me",
            style=discord.TextStyle.short,
        )
        self.add_item(self.emBio)

    async def on_submit(self, interaction: discord.Interaction):
        await _set_bio(interaction.user.id, self.emBio.value)
        await interaction.response.send_message(
            discord.Embed(
                description="Updated your bio! Check your status with `!status`",
                color=discord.Color.random,
            ),
            ephemeral=True,
        )


class Status(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="updatestatus")
    async def updatestatus(self, ctx):
        modal = StatusUpdateModal()
        await ctx.send_modal(modal)

    @commands.command(name="updatebio")
    async def updatebio(self, ctx):
        modal = BioUpdateModal()
        await ctx.send_modal(modal)

    @commands.command(aliases=["checkstatus", "getstatus"])
    async def status(self, ctx, member: discord.Member = None):
        if member is None:
            await _create_status_banner(ctx, ctx.author, _get_status(ctx.author.id))
        else:
            await _create_status_banner(ctx, member, _get_status(member.id))


async def setup(bot):
    await bot.add_cog(Status(bot))


##########################
# MONGODB HELPER FUNCTIONS


def _set_status(user_id: int, status: str, timestamp: str) -> None:
    USERS.find_one_and_update(
        {"_id": user_id},
        {"$set": {"status": status, "timestamp": timestamp}},
        upsert=True,
    )


def _set_bio(user_id: int, bio: str) -> None:
    USERS.find_one_and_update({"_id": user_id}, {"$set": {"bio": bio}}, upsert=True)


def _get_status(user_id: int) -> dict:
    query = USERS.find_one_and_update(
        {"_id": user_id},
        {"$setOnInsert": {"status": "", "bio": "No bio set.", "timestamp": "N/A"}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return {"status": query["status"], "bio": query["bio"], "timestamp": query["timestamp"]}


async def _create_status_banner(ctx, member, user_data):
    background = Editor("./imgs/sanrio.png")
    poppins_large = Font.poppins(size=38)
    poppins_medium = Font.poppins(size=30)
    poppins_small = Font.poppins(size=25)
    profile_picture = await load_image_async(str(member.display_avatar.url))
    profile = Editor(profile_picture).resize((150, 150)).circle_image()
    background.paste(profile, (30, 30))
    background.ellipse((30, 30), 150, 150, outline="#e0c3a4", stroke_width=2)
    background.text(
        (200, 50), f"{member.display_name}", font=poppins_large, color="white"
    )
    background.text(
        (200, 125),
        f"Status: {user_data["status"]}",
        font=poppins_medium,
        color="#FFFFFF",
    )
    background.text(
        (200, 175), f"Bio: {user_data["bio"]}", font=poppins_medium, color="#FFFFFF"
    )
    background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
    background.text(
        (200, 235),
        f"Last Modified: {user_data["timestamp"]}",
        font=Font.poppins(size=25),
        color="#FFFFFF",
    )
    with io.BytesIO() as image_binary:
        background.image.save(image_binary, format="PNG")
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="status_banner.png")
        await ctx.reply(file=file)
