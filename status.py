import discord
from discord.ext import commands
import requests
import asyncio
import json
from datetime import datetime

with open('config.json') as f:
    config = json.load(f)

TOKEN = config['token']
CHANNEL_NAME = config['channel_name']

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

async def fetch_status():
    status_response = requests.get('https://status.cfx.re/api/v2/status.json')
    components_response = requests.get('https://status.cfx.re/api/v2/components.json')
    metrics_response = requests.get('https://status.cfx.re/metrics-display/1hck2mqcgq3h/day.json')

    status_data = status_response.json()
    components_data = components_response.json()['components']
    metrics_data = metrics_response.json()

    return status_data, components_data, metrics_data

async def update_embed():
    await bot.wait_until_ready()

    downtime_start = None
    downtime_end = None
    last_message_id = None

    while not bot.is_closed():
        try:
            status_data, components_data, metrics_data = await fetch_status()
            channel = discord.utils.get(bot.get_all_channels(), name=CHANNEL_NAME)
            embed = discord.Embed(title="CFX Status", color=discord.Color.blurple())

            status_indicator = status_data.get('status', {}).get('indicator')

            if status_indicator == 'none':
                status_text = 'All Systems Operational'
                status_emoji = ':green_circle:'
                if downtime_start and downtime_end:
                    downtime_duration = (downtime_end - downtime_start).total_seconds() // 60
                    mention_message = f"@everyone CFX is back online after {downtime_duration} minutes of downtime. All operations are normal now."
                    downtime_start = None
                    downtime_end = None
                    await channel.send(mention_message)
            else:
                status_text = 'Experiencing Issues'
                status_emoji = ':orange_circle:'
                if not downtime_start:
                    downtime_start = datetime.now()
                    mention_message = f"@everyone CFX is currently facing issues and is not accessible. Please stay patient."
                    await channel.send(mention_message)

            embed.add_field(name="API Status", value=f"{status_emoji} {status_text}")

            component_lines = []
            for component in components_data:
                component_name = component.get('name')
                component_status = component.get('status')
                component_emoji = ':green_circle:' if component_status.lower() == 'operational' else ':red_circle:'
                component_line = f"{component_emoji} **{component_name}**: {component_status}"
                component_lines.append(component_line)

            embed.add_field(name="Component Status", value='\n'.join(component_lines), inline=False)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed.set_footer(text=f"Last updated at: {current_time}")

            if channel:
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
            print(f"An error occurred: {str(e)}")

        await asyncio.sleep(60)

@bot.event
async def on_ready():
    print('Bot is ready.')
    bot.loop.create_task(update_embed())

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please provide all the required arguments.')
    else:
        await ctx.send('An error occurred while executing the command.')

bot.run(TOKEN)
