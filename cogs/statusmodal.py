import os
import io
import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

# connect to MongoDB cluster
load_dotenv()
CLIENT = MongoClient(os.environ["MONGODB_URI"])

# initialize db collection
DB = CLIENT["muwu_data"]
USERS = DB["users"]

class Status(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Set your profile status")
    async def updatestatus(self, ctx):
        await ctx.send_modal(StatusUpdateModal())

    @discord.slash_command(description="Set your profile bio")
    async def updatebio(self, ctx):
        await ctx.send_modal(BioUpdateModal())

    @discord.slash_command(description="View your profile card")
    @discord.commands.option(name="user", type=discord.Member, required=False)
    async def status(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        user_data = _get_status(user.id)
        background = Editor("./imgs/sanrio.png")
        
        # fonts
        status_username = Font.poppins(variant="bold", size=38)
        status_info = Font.poppins(size=30)
        status_timestamp = Font.poppins(variant="italic", size=20)
        
        profile_picture = await load_image_async(str(user.display_avatar.url))
        profile = Editor(profile_picture).resize((150, 150)).circle_image()
        background.paste(profile, (30, 30))
        background.ellipse((30, 30), 150, 150, outline="#e0c3a4", stroke_width=2)
        background.text(
            (200, 50),
            f"{user.display_name}",
            font=status_username,
            color="white"
        )
        background.text(
            (200, 125),
            f"Status: {user_data["status"]}",
            font=status_info,
            color="#FFFFFF"
        )
        background.text(
            (200, 175),
            f"Bio: {user_data["bio"]}",
            font=status_info,
            color="#FFFFFF"
        )
        background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
        background.text(
            (200, 235),
            f"Last Modified: {user_data["timestamp"]}",
            font=status_timestamp,
            color="#FFFFFF"
        )
        with io.BytesIO() as image_binary:
            background.image.save(image_binary, format="PNG")
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="status_banner.png")
            await ctx.respond(file=file)
        

class StatusUpdateModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Set a status")
        self.emStatus = discord.ui.InputText(
            label="Status",
            min_length=1,
            max_length=40,
            required=True,
            placeholder="What's poppin?",
            style=discord.InputTextStyle.short
        )
        self.add_item(self.emStatus)

    async def callback(self, interaction: discord.Interaction):
        timePST = timezone("US/Pacific")
        timePSTnow = datetime.now(timePST)
        time_str = timePSTnow.strftime("%m/%d/%Y %H:%M:%S %Z")
        _set_status(interaction.user.id, self.emStatus.value, time_str)
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Updated your status! Check your status with `/status`",
                color=discord.Color.random(),
            ),
            ephemeral=True,
        )


class BioUpdateModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Set a user bio")
        self.emBio = discord.ui.InputText(
            label="Description",
            min_length=1,
            max_length=45,
            required=True,
            placeholder="About me",
            style=discord.InputTextStyle.short
        )
        self.add_item(self.emBio)

    async def callback(self, interaction: discord.Interaction):
        _set_bio(interaction.user.id, self.emBio.value)
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Updated your bio! Check your status with `/status`",
                color=discord.Color.random(),
            ),
            ephemeral=True,
        )

def setup(bot):
    bot.add_cog(Status(bot))


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
