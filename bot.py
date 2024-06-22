import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set up intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False

class MyBot(commands.Bot):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user}!')
        self.loop.create_task(update_embed(self))
        
        try:
            synced = await self.tree.sync()
            logging.info(f'Synced {len(synced)} command(s)')
        except Exception as e:
            logging.error(f'Error syncing commands: {e}')

# Instantiate the bot
bot = MyBot(intents=intents, command_prefix='!')

# Load configuration from file
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

TOKEN = os.getenv('DISCORD_TOKEN', config['token'])
CHANNEL_ID = config['channel_id']
CHANNEL_NAME = config['channel_name']
EDIT_CHANNEL = config['edit_channel_name']
REFRESH_INTERVAL = config['refresh_interval']

async def fetch_status():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://status.cfx.re/api/v2/status.json') as response:
                status_data = await response.json()
            async with session.get('https://status.cfx.re/api/v2/components.json') as response:
                components_data = await response.json()
                components_data = components_data['components']
            return status_data, components_data
        except Exception as e:
            logging.error(f"Error fetching status: {e}")
            return None, None

async def update_embed(bot):
    downtime_start, downtime_end, last_message_id = None, None, None
    embed_color, emoji = 6205745, '🟢'

    while not bot.is_closed():
        try:
            status_data, components_data = await fetch_status()
            if status_data is None or components_data is None:
                await asyncio.sleep(REFRESH_INTERVAL)
                continue

            channel = bot.get_channel(CHANNEL_ID)
            if channel is None:
                logging.error(f"Channel with ID {CHANNEL_ID} not found")
                await asyncio.sleep(REFRESH_INTERVAL)
                continue

            status_indicator = status_data.get('status', {}).get('indicator')

            if status_indicator == 'none':
                status_text = 'All Systems Operational'
                status_emoji = ':green_circle:'
                embed_color, emoji = 6205745, '🟢'
                if downtime_start and downtime_end:
                    downtime_duration = (downtime_end - downtime_start).total_seconds() // 60
                    mention_message = f"@everyone CFX is back online after {downtime_duration} minutes of downtime. All operations are normal now."
                    downtime_start, downtime_end = None, None
                    await channel.send(mention_message)
            else:
                status_text = 'Experiencing Issues'
                status_emoji = ':orange_circle:'
                embed_color, emoji = 16711680, '🔴'
                if not downtime_start:
                    downtime_start = datetime.now()
                    mention_message = f"@everyone CFX is currently facing issues and is not accessible. Please stay patient."
                    await channel.send(mention_message)

            embed = discord.Embed(title="CFX Status", color=embed_color)
            embed.add_field(name="API Status", value=f"{status_emoji} {status_text}")

            component_lines = [
                f":{'green_circle' if comp.get('status').lower() == 'operational' else 'red_circle'}: **{comp.get('name')}**: {comp.get('status')}"
                for comp in components_data
            ]

            embed.add_field(name="Component Status", value='\n'.join(component_lines), inline=False)
            embed.set_footer(text=f"Last updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            if EDIT_CHANNEL:
                await channel.edit(name=f'{emoji}︱{CHANNEL_NAME}')

            last_message = None
            if last_message_id:
                try:
                    last_message = await channel.fetch_message(last_message_id)
                except discord.errors.NotFound:
                    pass

            if last_message:
                try:
                    await last_message.edit(embed=embed)
                except discord.errors.Forbidden:
                    new_message = await channel.send(embed=embed)
                    last_message_id = new_message.id
            else:
                new_message = await channel.send(embed=embed)
                last_message_id = new_message.id
        except Exception as e:
            logging.error(f"An error occurred: {e}")

        await asyncio.sleep(REFRESH_INTERVAL)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please provide all the required arguments.')
    else:
        logging.error(f"An error occurred: {error}")
        await ctx.send('An error occurred while executing the command.')

# Run the bot
bot.run(TOKEN)
