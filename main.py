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

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    # Start the hourly tax task when the bot is ready
    channel = bot.get_channel(1274038617702006888)  # Replace with your channel ID
    bot.loop.create_task(hourly_tax(channel))

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
    with open("data.json", "w") as f:
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

# Your actual bot token
bot.run("YOUR_BOT_TOKEN_HERE")  # <- Your token here
