import discord
import os
import json
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
mute_list = []
client = discord.Client(intents = intents)

#insert bot token here
discord_token = ''

#loads json file with data for user point amounts
with open('userData.txt') as json_file:
    userDict = json.load(json_file)
    userDict = json.loads(userDict)

#class for bet object containing two sides and list of betters
class Bet:

    def __init__(self, side1: str, side2: str, betters1: dict, betters2: dict, open: bool):
        self.side1 = side1
        self.side2 = side2
        self.betters1 = betters1
        self.betters2 = betters2
        self.open = open

    #adds user to selected side of betters
    def add_better(self, side: str, user):
        if not self.open:
            return 'No bet is open'
        elif side == self.side1:
            if user.name not in self.betters1 and user.name not in self.betters2:
                self.betters1[user.name] = 0
                return str(user.name) + ' entered into bet'
            else:
                return 'User already entered bet'
        elif side == self.side2:
            if user.name not in self.betters1 and user.name not in self.betters2:
                self.betters2[user.name] = 0
                return str(user.name) + ' entered into bet'
            else:
                return 'User already entered bet'
        else:
            return "Side doesn't exist"

    #adds points to bet amount for user
    def add_bet(self, side, user, amount):
        if not self.open:
            return 'No bet is open'
        if side == self.side1:
            self.betters1[user] += int(amount)
            return amount + ' added to ' + user + "'s bet. Total bet is now " + str(self.betters1[user])
        elif side == self.side2:
            self.betters2[user] += int(amount)
            return amount + ' added to ' + user + "'s bet. Total bet is now " + str(self.betters2[user])
        else:
            return "Side doesn't exist"

    #check if user is in list of betters
    def check_better(self, user):
        if user in self.betters1 or user in self.betters2:
            return True
        else:
            return False

    #closes bet by deciding winner and distributes points
    def end_bet(self, side):
        if not self.open:
            return 'No bet is open'
        if side == self.side1:
            for user in self.betters1:
                userDict[user] += self.betters1[user]
            for user in self.betters2:
                userDict[user] -= self.betters2[user]
            self.open = False
            return 'Winner: ' + self.side1
        elif side == self.side2:
            for user in self.betters2:
                userDict[user] += self.betters2[user]
            for user in self.betters1:
                userDict[user] -= self.betters1[user]
            self.open = False
            return 'Winner: ' + self.side2
        else:
            return "Side doesn't exist"

    def send_side_from_side(self, side):
        if side == 'side1':
            return self.side1
        elif side == 'side2':
            return self.side2

    def send_side_from_user(self, user):
        if user in self.betters1:
            return self.side1
        elif user in self.betters2:
            return self.side2
        else:
            return None

bet = Bet('', '', {}, {}, False)

#message for bot joining
@client.event
async def on_ready():
    print('We have logged in as {0,user}'.format(client))

#bot waits for messages in discord channel
@client.event
async def on_message(message):

    #bot ignores own messages
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    #adds user to betting list
    if message.content.startswith('$start'):
        response = add_user(message.author)
        await message.channel.send(response)

    #sends user's current balance
    if message.content.startswith('$balance'):
        response = get_balance(message.author)
        await message.channel.send(response)

    #open a bet with two sides based on user replies
    if message.content.startswith('$open'):

        global bet

        if bet.open == True:
            await message.channel.send("Another bet is still open")
            return

        await message.channel.send("Send name for first side")

        def check(reply):
            return reply.content.startswith('$')

        try:
            side1 = await client.wait_for('message', check=check, timeout=60.0)

        except asyncio.TimeoutError:
            await message.channel.send('Timeout')

        except:
            await message.channel.send('Something broke')

        else:
            await message.channel.send("First bet added. Send name for second side")

            try:
                side2 = await client.wait_for('message', check=check, timeout=60.0)

            except asyncio.TimeoutError:
                await message.channel.send('Timeout')

            except:
                await message.channel.send('Something broke')

            else:
                await message.channel.send("Second bet added. Bet open for " + side1.content[1:] + " and " + side2.content[1:])
                open_bet(side1.content[1:], side2.content[1:])

    #allow users to join an ongoing bet
    if message.content.startswith('$join'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return

        await message.channel.send("Which side are you joining? (Type $1 or $2)")

        def check(reply):
            return reply.content.startswith('$')

        try:
            reply = await client.wait_for('message', check=check, timeout=60.0)
            if reply.content != '$1' and reply.content != '$2':
                raise Exception("Only $1 or $2")
            else:
                if reply.content.startswith('$1'):
                    side = get_side_from_side('side1')
                elif reply.content.startswith('$2'):
                    side = get_side_from_side('side2')
                response = join_bet(side, message.author)

        except asyncio.TimeoutError:
            await message.channel.send('Timeout')

        except:
            await message.channel.send('Something broke')

        else:
            await message.channel.send(response)

    #allows users to add points to ongoing bet that they have already joined
    if message.content.startswith('$add'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return

        if get_side_from_user(message.author.name) == None:
            await message.channel.send("You are not in the bet")
            return

        await message.channel.send("How much are you betting?")

        def check(reply):
            return reply.content.startswith('$')

        try:
            amount = await client.wait_for('message', check=check, timeout=60.0)
            side = get_side_from_user(message.author.name)
            if int(amount.content[1:]) < 0:
                await message.channel.send("Put a positive number")
                return
            if side == bet.side1:
                if int(amount.content[1:]) + bet.betters1[message.author.name] > userDict[message.author.name]:
                    await message.channel.send("You do not have this many points")
                    return
            elif side == bet.side2:
                if int(amount.content[1:]) + bet.betters2[message.author.name] > userDict[message.author.name]:
                    await message.channel.send("You do not have this many points")
                    return
            response = add_bet(side, message.author.name, amount.content[1:])

        except asyncio.TimeoutError:
            await message.channel.send('Timeout')

        except:
            await message.channel.send('Something broke')

        else:
            await message.channel.send(response)

    #closes ongoing bet and distributes points to betters
    if message.content.startswith('$close'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return

        await message.channel.send("Which side won? (Type $1 or $2)")

        def check(reply):
            return reply.content.startswith('$')

        try:
            reply = await client.wait_for('message', check=check, timeout=60.0)
            if reply.content != '$1' and reply.content != '$2':
                raise Exception("Only $1 or $2")
            else:
                if reply.content.startswith('$1'):
                    side = get_side_from_side('side1')
                elif reply.content.startswith('$2'):
                    side = get_side_from_side('side2')
                response = close_bet(side)

        except asyncio.TimeoutError:
            await message.channel.send('Timeout')

        except:
            await message.channel.send('Something broke')

        else:
            update_data()
            await message.channel.send(response)

    #gives user 1000 points if they have zero
    if message.content.startswith('$beg'):
        if userDict[message.author.name] <= 0:
            userDict[message.author.name] = 1000
            await message.channel.send(message.author.name + ' has been given 1000 points')
        else:
            await message.channel.send(message.author.name + ' still has points')

    #pay points to server mute user for one minute and remute if they attempt to unmute
    if message.content.startswith('$mute'):
        if userDict[message.author.name] < 1000:
            await message.channel.send('You do not have enough points')
            return
        else:
            await message.channel.send("Who are you muting? This will cost 1000 points")

            def check(reply):
                return reply.content.startswith('$')

            try:
                reply = await client.wait_for('message', check=check, timeout=60.0)
                if message.guild.get_member_named(reply.content[1:]) == None:
                    await message.channel.send('User does not exist in server')
                    return

            except asyncio.TimeoutError:
                await message.channel.send('Timeout')

            except:
                await message.channel.send('Something broke')

            else:
                user = message.guild.get_member_named(reply.content[1:])

                if user.voice == None:
                    await message.channel.send('User not in a voice channel')
                elif user.voice.channel:
                    await user.edit(mute=True)
                    global mute_list
                    mute_list.append(user)
                    change_points(-1000, message.author.name)
                    await message.channel.send(user.name + ' has been muted')
                    await asyncio.sleep(10)
                    mute_list.remove(user)
                    await user.edit(mute=False)
                    await message.channel.send(user.name + ' has been unmuted')

#bot waits for changes in voice state of members in discord call
@client.event
async def on_voice_state_update(member, before, after):

    #remutes server muted member if they attempt to unmute
    if member in mute_list:
        if before.mute == True and after.mute == False:
            await member.edit(mute=True)
    print(member, before.mute, after.mute)

#add points to bet for user
def add_bet(side, user, amount):
    global bet
    output = bet.add_bet(side, user, amount)
    return output

#initializes user into betting list by adding to json file and giving initial points
def add_user(user):
    if user.name not in userDict:
        userDict[user.name] = 1000
        userjson = json.dumps(userDict)
        with open('userData.txt', 'w') as outfile:
            json.dump(userjson, outfile)
        return user.name + ' has been given 1000 points'
    else:
        return user.name + ' already exists'

#obtains balance from user data
def get_balance(user):
    if user.name not in userDict:
        return 'User does not exist'
    else:
        return user.name + "'s balance is " + str(userDict[user.name])

#obtains name of requested side
def get_side_from_side(side):
    global bet
    output = bet.send_side_from_side(side)
    return output

#obtains name of side that user is in
def get_side_from_user(user):
    global bet
    output = bet.send_side_from_user(user)
    return output

#adds user to list of betters
def join_bet(side,user):
    global bet
    output = bet.add_better(side,user)
    return output

#opens bet with two sides
def open_bet(side1,side2):
    global bet
    bet = Bet(side1,side2,{},{},True)

#closes bet and distributes points
def close_bet(side):
    global bet
    output = bet.end_bet(side)
    return output

#updates user data in txt file
def update_data():
    userjson = json.dumps(userDict)
    with open('userData.txt', 'w') as outfile:
        json.dump(userjson, outfile)

#changes amount of points that a user has and updates txt file
def change_points(amount, user):
    userDict[user] += amount
    update_data()

client.run(discord_token)
