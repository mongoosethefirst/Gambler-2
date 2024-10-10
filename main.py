import discord
import random
import json
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='>', intents=intents)

# Dictionary to store user balances
user_balances = {}
# Dictionary to store stock data
stock_prices = {
    'apple': 100,
    'tesla': 150,
    'google': 200,
}

# Dictionary to store user stocks
user_stocks = {}

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    # Start the hourly tax task when the bot is ready
    channel = bot.get_channel(1274038617702006888)  # Replace with your channel ID
    bot.loop.create_task(hourly_tax(channel))
    bot.loop.create_task(update_stock_prices())

async def hourly_tax(channel):
    while True:
        # Check if data.json exists, create it if it doesn't
        try:
            with open("data.json", "r") as f:
                d = json.load(f)
        except FileNotFoundError:
            d = {}  # Start with an empty dictionary if the file doesn't exist

        # Apply tax to each user
        for user_id, user_data in d.items():
            if "money" in user_data:  # Ensure the 'money' key exists
                tax = int(user_data["money"] * 0.02)  # 2% tax on the user's current money
                user_data["money"] -= tax

                # Fetch the member by ID to get the username
                member = channel.guild.get_member(int(user_id))
                if member:
                    await channel.send(f"{member.name}, you lost ${tax} as tax!")
                else:
                    await channel.send(f"User with ID {user_id} is not in the server.")

        # Save changes to data.json
        with open("data.json", "w") as f:
            json.dump(d, f, indent=4)

        await asyncio.sleep(300)  # Run every 5 minutes (300 seconds)

async def update_stock_prices():
    while True:
        # Randomly fluctuate stock prices between -10% to +10%
        for stock in stock_prices:
            change_percent = random.uniform(-0.1, 0.1)  # -10% to +10%
            stock_prices[stock] = max(1, int(stock_prices[stock] * (1 + change_percent)))

        await asyncio.sleep(600)  # Update every 10 minutes

@bot.command(name='beg')
async def beg(ctx):
    user_id = str(ctx.author.id)  # Store user ID as a string for JSON compatibility

    amount = random.randint(1, 20)  # Random amount between 1 and 20

    # Update the user's balance
    if user_id in user_balances:
        user_balances[user_id] += amount
    else:
        user_balances[user_id] = amount

    # Load user data from data.json to update the file
    try:
        with open("data.json", "r") as f:
            d = json.load(f)
    except FileNotFoundError:
        d = {}

    # Update user balance in data
    if user_id not in d:
        d[user_id] = {"money": 0}
    d[user_id]["money"] += amount

    # Save changes to data.json
    with open(".data.json", "w") as f:
        json.dump(d, f, indent=4)

    await ctx.send(f"{ctx.author.name} begged and received ${amount}.")

@bot.command(name='bank')
async def bank(ctx):
    user_id = str(ctx.author.id)  # Store user ID as a string for JSON compatibility
    balance = user_balances.get(user_id, 0)  # Default to 0 if user not found

    await ctx.send(f"{ctx.author.name}'s Bank Balance: ${balance}.")

@bot.command(name='slots')
async def slots(ctx):
    user_id = str(ctx.author.id)

    # Check if user has enough money to play
    if user_balances.get(user_id, 0) < 10:
        await ctx.send("You don't have enough money to play slots! It costs $10.")
        return

    # Deduct $10 from the user's balance
    user_balances[user_id] -= 10

    # Load user data from data.json to update the file
    try:
        with open("data.json", "r") as f:
            d = json.load(f)
    except FileNotFoundError:
        d = {}

    if user_id not in d:
        d[user_id] = {"money": 0}
    d[user_id]["money"] = user_balances[user_id]

    # Define the reward probabilities
    rewards = [0] * 50 + [5] * 25 + [10] * 10 + [50] * 5 + [100, 150, 200, 250, 300, 350, 400, 450, 500, 550]
    reward = random.choice(rewards)

    # Add the reward to the user's balance
    user_balances[user_id] += reward
    d[user_id]["money"] += reward

    # Save changes to data.json
    with open("data.json", "w") as f:
        json.dump(d, f, indent=4)

    await ctx.send(f"{ctx.author.name} rolled slots and got ${reward}!")

@bot.command(name='give')
async def give(ctx, member: discord.Member, amount: int):
    giver_id = str(ctx.author.id)
    receiver_id = str(member.id)

    # Ensure the amount is positive
    if amount <= 0:
        await ctx.send("You must give a positive amount!")
        return

    # Check if the giver has enough money
    if user_balances.get(giver_id, 0) < amount:
        await ctx.send("You don't have enough money to give!")
        return

    # Deduct the amount from the giver's balance and add it to the receiver's
    user_balances[giver_id] -= amount
    if receiver_id in user_balances:
        user_balances[receiver_id] += amount
    else:
        user_balances[receiver_id] = amount

    # Update data.json for both users
    try:
        with open("data.json", "r") as f:
            d = json.load(f)
    except FileNotFoundError:
        d = {}

    if giver_id in d:
        d[giver_id]["money"] = user_balances[giver_id]
    else:
        d[giver_id] = {"money": user_balances[giver_id]}

    if receiver_id in d:
        d[receiver_id]["money"] = user_balances[receiver_id]
    else:
        d[receiver_id] = {"money": user_balances[receiver_id]}

    with open("data.json", "w") as f:
        json.dump(d, f, indent=4)

    await ctx.send(f"{ctx.author.name} gave ${amount} to {member.name}.")

@bot.command(name='stock')
async def stock(ctx, action: str, stock_name: str = None, amount: int = None):
    user_id = str(ctx.author.id)

    if action == 'check':
        # Display the current stock prices
        prices = [f"{stock}: ${price}" for stock, price in stock_prices.items()]
        await ctx.send("\n".join(prices))
    elif action == 'buy':
        if stock_name not in stock_prices:
            await ctx.send("Invalid stock name!")
            return
        if amount is None or amount <= 0:
            await ctx.send("You must specify a valid number of stocks to buy!")
            return

        total_cost = stock_prices[stock_name] * amount

        # Check if user has enough money to buy stocks
        if user_balances.get(user_id, 0) < total_cost:
            await ctx.send("You don't have enough money to buy these stocks!")
            return

        # Deduct money and add stocks
        user_balances[user_id] -= total_cost
        if user_id not in user_stocks:
            user_stocks[user_id] = {}
        user_stocks[user_id][stock_name] = user_stocks[user_id].get(stock_name, 0) + amount

        await ctx.send(f"{ctx.author.name} bought {amount} shares of {stock_name} for ${total_cost}.")
    elif action == 'sell':
        if stock_name not in stock_prices:
            await ctx.send("Invalid stock name!")
            return
        if amount is None or amount <= 0:
            await ctx.send("You must specify a valid number of stocks to sell!")
            return

        # Check if the user owns enough stocks to sell
        if user_stocks.get(user_id, {}).get(stock_name, 0) < amount:
            await ctx.send("You don't have enough stocks to sell!")
            return

        total_gain = stock_prices[stock_name] * amount

        # Add money and remove stocks
        user_balances[user_id] += total_gain
        user_stocks[user_id][stock_name] -= amount
        if user_stocks[user_id][stock_name] == 0:
            del user_stocks[user_id][stock_name]  # Remove stock if 0

        await ctx.send(f"{ctx.author.name} sold {amount} shares of {stock_name} for ${total_gain}.")
    else:
        await ctx.send("Invalid action! Use 'check', 'buy', or 'sell'.")

@bot.command(name='help')
async def help_command(ctx):
    help_message = """
    **Available Commands:**
    >beg - Beg for money and receive a random amount.
    >bank - Check your current balance.
    >slots - Play slots for $10. Win random rewards.
    >give [user] [amount] - Give a user some money.
    >stock check - Check current stock prices.
    >stock buy [stock_name] [amount] - Buy stocks.
    >stock sell [stock_name] [amount] - Sell stocks.
    """
    await ctx.send(help_message)

# Your actual bot token
bot.run("YOUR_BOT_TOKEN_HERE")  # <- Your token here
