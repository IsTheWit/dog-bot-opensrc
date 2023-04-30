import os
from io import BytesIO
import aiohttp
from nextcord.ext import tasks, commands
import json, random, datetime, asyncio
from PIL import Image, ImageFont, ImageDraw
import textwrap
from nextcord import File, ButtonStyle, Embed, Color, SelectOption, Intents, Interaction, SlashOption
from nextcord.ui import Button, View, Select
import nextcord
from timeit import default_timer
import logging
import logger
from queue import SimpleQueue as Queue
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True

roulette_queue = Queue()  # Awaiting users (normally, shouldn't be more than 1 at the same time)
current_roulette_dialogs = []  # Current pairs, you have to iterate through them for every message the bot gets in some function


logger.setupLogging()

with open('token.txt', 'r', encoding='utf-8') as contents:
    TOKEN = contents.read()
    
links = json.load(open("gifs.json"))
helpGuide = json.load(open("help.json"))
earlyAccessIDs = [804061657625395241, 296735247213789215]

_log = logging.getLogger(__name__)

uses = 0
cooldown = 0

bot = commands.Bot(command_prefix="dog ", intents=intents)
bot.remove_command("help")

def createHelpEmbed(pageNum=0, inline=False):
  pageNum = pageNum % len(list(helpGuide))
  pageTitle = list(helpGuide)[pageNum]
  embed=Embed(color=0x0080ff, title=pageTitle)
  for key, val in helpGuide[pageTitle].items():
    embed.add_field(name=key, value=val, inline=inline)
    embed.set_footer(text=f"Page {pageNum+1} of {len(list(helpGuide))}")
  return embed  
  
def uwuify(text):
    text = text.replace('e', 'uwu')
    try:
        from pyperclip import copy
        copy(text)
    except:
        pass
    return text  

@commands.cooldown(uses, cooldown, commands.BucketType.user)
@bot.command(name="help")
async def help(ctx):
  currentPage = 0

  async def next_callback(interaction):
    nonlocal currentPage, sent_msg
    currentPage += 1
    await sent_msg.edit(embed=createHelpEmbed(pageNum=currentPage), view=myview)
  
  async def previous_callback(interaction):
    nonlocal currentPage, sent_msg
    currentPage -= 1
    await sent_msg.edit(embed=createHelpEmbed(pageNum=currentPage), view=myview)
  
  nextButton = Button(label=">", style=ButtonStyle.blurple)
  nextButton.callback = next_callback
  previousButton = Button(label="<", style=ButtonStyle.blurple)
  previousButton.callback = previous_callback

  myview = View(timeout=180)
  myview.add_item(previousButton)
  myview.add_item(nextButton)
  sent_msg = await ctx.send(embed=createHelpEmbed(pageNum=0), view=myview)

@commands.cooldown(uses, cooldown, commands.BucketType.user)
@bot.command(name="hi")
async def hi(ctx):
  
  async def dropdown_callback(interaction):
    for value in dropdown.values:
      await ctx.send(random.choice(links[value]))
  
  option1 = SelectOption(label="chill", value="gif", description="doggo is lonely", emoji="😎")
  option2 = SelectOption(label="play", value="play", description="doggo is bored", emoji="🙂")
  option3 = SelectOption(label="feed", value="feed", description="doggo is hungry", emoji="😋")
  dropdown = Select(placeholder="What would you like to do with doggo?", options=[option1, option2, option3], max_values=3)

  dropdown.callback = dropdown_callback
  myview = View(timeout=180)
  myview.add_item(dropdown)
  await ctx.send('Hello!', view=myview)

@bot.command(name="pic")
@commands.cooldown(uses, cooldown, commands.BucketType.user)
async def pic(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dog.ceo/api/breeds/image/random") as request:
            await ctx.send((await request.json())["message"])

@commands.cooldown(uses, cooldown, commands.BucketType.user)
@bot.command(name="gif", aliases=["feed", "play", "sleep"])
async def gif(ctx):
	await ctx.send(random.choice(links[ctx.invoked_with]))


async def schedule_daily_message(h, m, s, msg, channelid):
	while True:
		now = datetime.datetime.now()
		# then = now+datetime.timedelta(days=1)
		then = now.replace(hour=h, minute=m, second=s)
		if then < now:
			then += datetime.timedelta(days=1)
		wait_time = (then-now).total_seconds()
		await asyncio.sleep(wait_time)

		channel = bot.get_channel(channelid)

		await channel.send(msg)
		await channel.send(random.choice(links["play"]))
		await asyncio.sleep(1)

# dog daily "good morning" 8 30

@commands.cooldown(uses, cooldown, commands.BucketType.user)
@bot.command(name="daily")
async def daily(ctx, mystr:str, hour:int, minute:int, second:int):
	_log.info(mystr, hour, minute, second)

	if not (0 < hour < 24 and 0 <= minute <= 60 and 0 <= second < 60):
		raise commands.BadArgument()

	time = datetime.time(hour, minute, second)
	timestr = time.strftime("%I:%M:%S %p")
	await ctx.send(f"A daily message will be sent at {timestr} everyday in this channel.\nDaily message:\"{mystr}\"\nConfirm by simply saying: `yes`")
@daily.error
async def daily_error(ctx, error):
	if isinstance(error, commands.BadArgument):
		await ctx.send("""Incorrect format. Use the command this way: `dog daily "message" hour minute second`.
For example: `dog daily "good morning" 22 30 0` for a message to be sent at 10:30 everyday""")

# dog speak hello world!!

# @bot.command(name='speak')
async def speakOld(ctx, *args):
	msg = " ".join(args)
	font = ImageFont.truetype("PatrickHand-Regular.ttf", 50)
	img = Image.open("dog.jpg")
	cx, cy = (350, 230)
	
	lines = textwrap.wrap(msg, width=20)
	_log.info(lines)
	w, h = font.getsize(msg)
	y_offset = (len(lines)*h)/2
	y_text = cy-(h/2) - y_offset

	for line in lines:
		draw = ImageDraw.Draw(img)
		w, h = font.getsize(line)
		draw.text((cx-(w/2), y_text), line, (0, 0, 0), font=font)
		img.save("dog-edited.jpg")
		y_text += h
	
	with open("dog-edited.jpg", "rb") as f:
		img = File(f)
		await ctx.channel.send(file=img)
	
@bot.slash_command()
@commands.cooldown(uses, cooldown, commands.BucketType.user)
async def speak(interaction: Interaction, msg:str, fontSize: int = SlashOption(name="picker", choices={"30pt" : 30, "50pt" : 50, "70pt" : 70}), fontPicker : str = SlashOption(name="font", choices={"Patrick Hand Regular": "PatrickHand-Regular.ttf", "Futura Condensed Bold" : "FuturaCondensed-Bold.ttf", "Comic Sans" : "comic.ttf"})):
	font = ImageFont.truetype(fontPicker, fontSize)
	img = Image.open("dog.jpg")
	cx, cy = (350, 230)
	
	lines = textwrap.wrap(msg, width=20)
	w, h = font.getsize(msg)
	y_offset = (len(lines)*h)/2
	y_text = cy-(h/2) - y_offset

	for line in lines:
		draw = ImageDraw.Draw(img)
		w, h = font.getsize(line)
		draw.text((cx-(w/2), y_text), line, (0, 0, 0), font=font)
		img.save("dog-edited.jpg")
		y_text += h
	
	with open("dog-edited.jpg", "rb") as f:
		img = File(f)
		await interaction.response.send_message(file=img)
	
	
@bot.command(name='support')
@commands.cooldown(uses, cooldown, commands.BucketType.user)
async def support(ctx):
  # this is unused
  hi = Button(label="click me", style=ButtonStyle.blurple)
  subscribe = Button(label="subscribe", url="https://www.youtube.com/channel/UCu-PhjjYY5IP9UVhBs9niLw?sub_confirmation=1")
  
  async def hi_callback(interaction):
    await interaction.response.send_message("Hello!")
    
  hi.callback = hi_callback

  myview = View(timeout=180)
  myview.add_item(hi)
  myview.add_item(subscribe)

  await ctx.send("hi", view=myview)

@bot.command(name='ping')
@commands.cooldown(uses, cooldown, commands.BucketType.user)
async def ping(ctx):
    msg1 = 'Ping...'
    time1 = default_timer()
    msg = await ctx.send(msg1)
    time2 = default_timer()
    latency = round((time2 - time1)*1000)
    msg2 = f'Pong! | {latency}ms'
    await msg.edit(content=msg2)
    _log.info(f'{ctx.author} pinged the bot in #{ctx.channel} ({ctx.guild}). Latency: {latency}ms.')

@bot.slash_command(name='generate')
async def generator(interaction: Interaction, msg:str):
    imgs = []
    urls = [f"https://www.demirramon.com/utgen.png?message={msg}"]
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls):
            async with session.get(url) as resp:
                bytes = BytesIO(await resp.read())
                imgs.append(nextcord.File(bytes, filename=f'pic{i}.png', force_close=True))
    _log.info(f'{interaction.user} generated "{msg}" ({interaction.guild})')            
    await interaction.response.send_message(files=imgs)
    
@bot.command(name='gun')
@commands.cooldown(uses, cooldown, commands.BucketType.user)
async def gun(ctx):
    await ctx.send("<:totallyjustanerfgun:1064957418548764672>")
    _log.info(f'doggo pulled out a gun in {ctx.guild}')

@bot.command(name='chatroulette')
async def chatroulette(ctx):
  person1 = ctx.author
  await ctx.send("DM me when you think another person has entered the chat roulette queue!")
  if roulette_queue.empty():
      roulette_queue.put(person1.id)
      _log.info(f"{person1.id} was added into the anon chat queue.")
      return
  person2 = roulette_queue.get()
  if person2 == person1.id:
      _log.error(f"{person1.id} has tried to add themselves into the queue more than once.")
      return   
  current_roulette_dialogs.append((person1.id, person2))
  
@bot.command(name='middle')
async def middle(ctx):
    with open("mf.mp4", "rb") as f:
        vid = File(f)
        await ctx.send(file=vid)
        
@bot.slash_command(name='uwuify')
async def uwu(interaction: Interaction, msg:str):
    uwuified = uwuify(msg)
    await interaction.response.send_message(uwuified)

@bot.listen('on_message')
async def roulette_listener(message):
    # Checking if there are current pairs and whether the message was sent in a server
    if not current_roulette_dialogs or message.guild is not None:
        # If there are no pairs or it was in a server, just exit the function
        return

    for pair in current_roulette_dialogs:
        if message.author.id not in pair:
            continue  # If the pair doesn't include current user, check another pair
        person2 = (await bot.fetch_user(pair[1])) if message.author.id == pair[0] else (await bot.fetch_user(pair[0]))
        await person2.send(message.content)  
    
class servercounter(commands.Cog):
  def __init__(self):
      self.servercount.start()

  def cog_unload(self):
      self.servercount.cancel()

  @tasks.loop(seconds=1.0)
  async def servercount(self):
    guildnum = len(bot.guilds)
    activity = nextcord.Game(name=f"in {guildnum} servers!")
    await bot.change_presence(status=nextcord.Status.online, activity=activity)    

@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandOnCooldown):
    em = Embed(title=f"Slow it down!",description=f"Try again in {error.retry_after:2f}s.", color=Color.red())
    _log.warn('cooldown activated')
    await ctx.send(embed=em)
  
@bot.event
async def on_ready():
  _log.info(f"Logged in as: {bot.user.name}")
  activity = nextcord.Game(name="It's been a while, hasn't it?")
  await bot.change_presence(status=nextcord.Status.online, activity=activity)
  # bot.add_cog(servercounter())

bot.run(TOKEN)
