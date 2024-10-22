import discord
import random
import json
import asyncio
from discord.ext import commands, tasks

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)

# File names for persistence
BALANCE_FILE = 'user_balances.json'
SUGGESTIONS_FILE = 'user_suggestions.json'
STOCKS_FILE = 'user_stocks.json'

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

user_balances = load_data(BALANCE_FILE)
user_suggestions = load_data(SUGGESTIONS_FILE)
user_stocks = load_data(STOCKS_FILE)
user_cooldowns = {}

def round_to_cents(value):
    return round(value, 2)

def get_user_balance(user_id):
    return round_to_cents(user_balances.get(user_id, 0))

def set_user_balance(user_id, amount):
    user_balances[user_id] = round_to_cents(amount)
    save_data(BALANCE_FILE, user_balances)

async def cooldown_check(ctx):
    user_id = ctx.author.id
    last_command = user_cooldowns.get(user_id, 0)
    elapsed = asyncio.get_event_loop().time() - last_command

    if elapsed < 3:
        await ctx.send(f"Please wait {round(3 - elapsed, 1)} more seconds.")
        return False

    user_cooldowns[user_id] = asyncio.get_event_loop().time()
    return True

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    hourly_rewards.start()  # Start the hourly rewards task

    channel = discord.utils.get(bot.get_all_channels(), name='general')
    if channel:
        await channel.send("Hello, World! State: Online")
    else:
        print("Channel not found. Make sure you have the correct channel name.")

@tasks.loop(hours=1)
async def hourly_rewards():
    """Give each user $150 every hour."""
    for user_id in user_balances.keys():
        set_user_balance(user_id, get_user_balance(user_id) + 150)
    print("Hourly rewards distributed.")

@bot.command(name='commands')
async def commands(ctx):
    command_list = """
**Available Commands:**
1. **>bank** - Check your bank balance.
2. **>beg** - Beg for some money.
3. **>slots** - Play slots for $10.
4. **>checkstock** - Check available stocks and their prices.
5. **>buystock <stock_name> <amount>** - Buy shares of a stock.
6. **>sellstock <stock_name> <amount>** - Sell shares of a stock.
7. **>suggestion <your suggestion>** - Suggest something for the server.
8. **>ranks** - View the top users by balance.
9. **>coinflip <bet> <heads/tails>** - Play a coin flip game to double or lose your money.
10. **>commands** - Display this list of commands.
"""
    await ctx.send(command_list)

@bot.command(name='bank')
async def bank(ctx):
    if not await cooldown_check(ctx):
        return

    user_id = str(ctx.author.id)
    balance = get_user_balance(user_id)
    await ctx.send(f"{ctx.author.name}'s Bank Balance: ${balance}.")

@bot.command(name='beg')
async def beg(ctx):
    if not await cooldown_check(ctx):
        return

    user_id = str(ctx.author.id)
    amount = random.randint(1, 20)
    set_user_balance(user_id, get_user_balance(user_id) + amount)
    await ctx.send(f"{ctx.author.name} begged and received ${amount}!")

@bot.command(name='slots')
async def slots(ctx):
    if not await cooldown_check(ctx):
        return

    user_id = str(ctx.author.id)
    if get_user_balance(user_id) < 10:
        await ctx.send("You don't have enough money to play slots! It costs $10.")
        return

    set_user_balance(user_id, get_user_balance(user_id) - 10)
    rewards = [0] * 50 + [5] * 25 + [10] * 10 + [50] * 5 + [100, 150, 200, 250, 300, 350, 400, 450, 500, 550]
    reward = random.choice(rewards)
    set_user_balance(user_id, get_user_balance(user_id) + reward)

    await ctx.send(f"{ctx.author.name} rolled slots and got ${reward}!")

@bot.command(name='coinflip')
async def coinflip(ctx, bet: int, choice: str):
    if not await cooldown_check(ctx):
        return

    user_id = str(ctx.author.id)
    choice = choice.lower()

    if choice not in ["heads", "tails"]:
        await ctx.send("Invalid choice! Please choose 'heads' or 'tails'.")
        return

    if get_user_balance(user_id) < bet:
        await ctx.send("You don't have enough money to make that bet.")
        return

    outcome = random.choice(["heads", "tails"])

    if choice == outcome:
        winnings = bet * 2
        set_user_balance(user_id, get_user_balance(user_id) + winnings)
        await ctx.send(f"It's {outcome}! 🎉 You won ${winnings}!")
    else:
        set_user_balance(user_id, get_user_balance(user_id) - bet)
        await ctx.send(f"It's {outcome}. You lost ${bet}. Better luck next time!")

@bot.command(name='checkstock')
async def checkstock(ctx):
    stocks = {
        "apple": 175.54, "google": 138.12, "amazon": 129.43,
        "microsoft": 327.41, "tesla": 254.31
    }

    stock_list = "**Available Stocks and Prices:**\n"
    for stock, price in stocks.items():
        stock_list += f"{stock.capitalize()}: ${price}\n"

    await ctx.send(stock_list)

@bot.command(name='buystock')
async def buystock(ctx, stock_name: str, amount: int):
    stocks = {"apple": 175.54, "google": 138.12}
    user_id = str(ctx.author.id)

    if stock_name.lower() not in stocks:
        await ctx.send("Invalid stock name.")
        return

    total_cost = stocks[stock_name.lower()] * amount
    if get_user_balance(user_id) < total_cost:
        await ctx.send("You don't have enough money.")
        return

    set_user_balance(user_id, get_user_balance(user_id) - total_cost)
    await ctx.send(f"Bought {amount} shares of {stock_name.capitalize()}.")

@bot.command(name='sellstock')
async def sellstock(ctx, stock_name: str, amount: int):
    stocks = {"apple": 175.54}
    user_id = str(ctx.author.id)

    total_value = stocks[stock_name.lower()] * amount
    set_user_balance(user_id, get_user_balance(user_id) + total_value)
    await ctx.send(f"Sold {amount} shares of {stock_name.capitalize()}.")

@bot.command(name='suggestion')
async def suggestion(ctx, *, suggestion_text: str):
    user_suggestions[str(ctx.author.id)] = suggestion_text
    save_data(SUGGESTIONS_FILE, user_suggestions)
    await ctx.send(f"Suggestion recorded: {suggestion_text}")

@bot.command(name='ranks')
async def ranks(ctx):
    if not user_balances:
        await ctx.send("No one has any money yet!")
        return

    sorted_balances = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    leaderboard = "**Leaderboard - Top Users by Balance:**\n"
    for rank, (user_id, balance) in enumerate(sorted_balances, 1):
        user = await bot.fetch_user(int(user_id))
        leaderboard += f"{rank}. {user.name}: ${balance}\n"

    await ctx.send(leaderboard)

bot.run('YOUR_BOT_TOKEN_HERE')
