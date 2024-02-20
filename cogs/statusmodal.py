import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font, Canvas
from datetime import datetime
from pytz import timezone
import io
import sqlite3


class StatusChangeModal(discord.ui.Modal):

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
    timePST = timezone('US/Pacific')
    timePSTnow = datetime.now(timePST)
    time_str = timePSTnow.strftime('%m/%d/%Y %H:%M:%S %Z')
    print(f"Status: {self.emStatus.value}")
    print(f"Bio: {self.emBio.value}")
    print(f"Bio: {time_str}")
    await add_status(interaction.user.mention, self.emStatus.value,
                     self.emBio.value, time_str)
    await interaction.response.send_message(
        "Your status is updated. Use <!status @user>", ephemeral=True)


class StatusModalCog(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command(name="changestatus")
  async def change_status(self, ctx):
    modal = StatusChangeModal()
    await ctx.send_modal(modal)


async def setup(bot):
  await bot.add_cog(StatusModalCog(bot))


##########################
#DB Helper Functions
async def add_status(user, status='', bio='', timestamp=''):
  user = user[2:-1]
  conn = sqlite3.connect('uwustatus.db')
  c = conn.cursor()
  c.execute('''
    CREATE TABLE IF NOT EXISTS statuses (
      user_id TEXT PRIMARY KEY,
      Status TEXT,
      Bio TEXT,
      Timestamp TEXT
    )
  ''')
  c.execute(
      '''
      INSERT INTO statuses (user_id, Status, Bio, Timestamp) 
      VALUES (?, ?, ?, ?)
      ON CONFLICT(user_id) 
      DO UPDATE SET Status=excluded.Status, Bio=excluded.Bio, Timestamp=excluded.Timestamp''',
      (user, status, bio, timestamp))
  conn.commit()
  conn.close()
  return True


async def get_status_data():
  conn = sqlite3.connect('uwustatus.db')
  c = conn.cursor()
  c.execute('SELECT * FROM statuses')
  statuses = {
      row[0]: {
          'Status': row[1],
          'Bio': row[2],
          'Timestamp': row[3]
      }
      for row in c.fetchall()
  }
  conn.close()
  return statuses


async def statusbanner(text, member, user_data):
  background = Editor("./imgs/sanrio.png")
  poppins_large = Font.poppins(size=38)
  poppins_medium = Font.poppins(size=30)
  poppins_small = Font.poppins(size=25)
  profile_picture = await load_image_async(str(member.display_avatar.url))
  profile = Editor(profile_picture).resize((150, 150)).circle_image()
  background.paste(profile, (30, 30))
  background.ellipse((30, 30), 150, 150, outline="#e0c3a4", stroke_width=2)
  background.text((200, 50),
                  f"{member.display_name}",
                  font=poppins_large,
                  color="white")
  background.text((200, 125),
                  f"Status: {user_data['Status']}",
                  font=poppins_medium,
                  color="#FFFFFF")
  background.text((200, 175),
                  f"Bio: {user_data['Bio']}",
                  font=poppins_medium,
                  color="#FFFFFF")
  background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
  background.text((200, 235),
                  f"Last Modified: {user_data['Timestamp']}",
                  font=Font.poppins(size=25),
                  color="#FFFFFF")
  with io.BytesIO() as image_binary:
    background.image.save(image_binary, format="PNG")
    image_binary.seek(0)
    file = discord.File(fp=image_binary, filename="status_banner.png")
    await text.send(file=file)
