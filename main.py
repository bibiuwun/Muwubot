import os, discord
from discord.ext import commands, bridge
from dotenv import load_dotenv

load_dotenv()

COGS = ["welcome", "statusmodal", "gamble"]
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

muwubot = bridge.Bot(command_prefix="!", intents=INTENTS)
for cog in COGS:
    muwubot.load_extension(f"cogs.{cog}")


@muwubot.event
async def on_ready():
    print("MuwuBot is Online")


if __name__ == "__main__":
    # load bot token
    muwubot.run(os.environ["TOKEN"])
