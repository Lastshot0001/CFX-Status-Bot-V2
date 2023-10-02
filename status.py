import discord
from discord.ext import commands
import requests, asyncio, json
from datetime import datetime

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

class myBot(commands.Bot):
    async def on_ready(self):
        await self.wait_until_ready()
        print(f'Logged in as {self.user}!')

        self.loop.create_task(update_embed())
        
        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} Command(s)')
        except Exception as e:
            print('e: {}'.format(e))

bot = myBot(intents = intents, command_prefix = '!')

with open('config.json') as f:
    config = json.load(f)

with open('message.json') as f:
    messageId = json.load(f)

async def set_json_file(dict):
    json.dump(dict, open('message.json', 'w', encoding = 'utf8'), indent = 4, ensure_ascii = False)

async def fetch_status():
    status_response = requests.get('https://status.cfx.re/api/v2/status.json')
    components_response = requests.get('https://status.cfx.re/api/v2/components.json')

    status_data = status_response.json()
    components_data = components_response.json()['components']
    return status_data, components_data

async def update_embed():
    downtime_start, downtime_end, last_downtime_message = None, None, None

    while not bot.is_closed():
        try:
            status_data, components_data = await fetch_status()
            channel = bot.get_channel(config['channel_id'])

            status_indicator = status_data.get('status', {}).get('indicator')

            if status_indicator == 'none':
                status_text = 'All Systems Operational'
                status_emoji = ':green_circle:'
                embed_color, emoji = 6205745, '🟢'
                if downtime_start:
                    downtime_end = datetime.now()
                    downtime_duration = (downtime_end - downtime_start).total_seconds() // 60
                    mention_message = f"@everyone CFX is back online after {downtime_duration} minutes of downtime. All operations are normal now."
                    downtime_start = None
                    downtime_end = None
                    if last_downtime_message:
                        await last_downtime_message.delete()
                    last_downtime_message = await channel.send(mention_message)
            else:
                status_text = 'Experiencing Issues'
                status_emoji = ':orange_circle:'
                embed_color, emoji = 16711680, '🔴'
                if not downtime_start:
                    downtime_start = datetime.now()
                    mention_message = f"@everyone CFX is currently facing issues and is not accessible. Please stay patient."
                    if last_downtime_message:
                        await last_downtime_message.delete()
                    last_downtime_message = await channel.send(mention_message)

            embed = discord.Embed(title="CFX Status", color=embed_color)
            embed.add_field(name="API Status", value=f"{status_emoji} {status_text}")

            component_lines = []
            for component in components_data:
                component_name = component.get('name')
                component_status = component.get('status')
                component_emoji = ':green_circle:' if component_status.lower() == 'operational' else ':red_circle:'
                component_line = f"{component_emoji} **{component_name}**: {component_status}"
                component_lines.append(component_line)

            embed.add_field(name="Component Status", value='\n'.join(component_lines), inline=False)
            embed.set_thumbnail(url = 'https://dka575ofm4ao0.cloudfront.net/pages-transactional_logos/retina/219915/cfxre-shadow.png')

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed.set_footer(text=f"Last updated at: {current_time}")

            if channel:
                if config['edit_channel_name']:
                    channel_name = config['channel_name']
                    await channel.edit(name = f'{emoji}︱{channel_name}')

                last_message = None

                if messageId['id']:
                    try:
                        last_message = await channel.fetch_message(messageId['id'])
                    except discord.errors.NotFound:
                        pass

                if last_message:
                    try:
                        await last_message.edit(embed=embed)
                    except discord.errors.Forbidden:
                        pass
                else:
                    new_message = await channel.send(embed=embed)
                    messageId['id'] = new_message.id
                    await set_json_file(messageId)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

        await asyncio.sleep(config['refresh_interval'])

bot.run(config['token'])