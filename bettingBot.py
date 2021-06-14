import discord
import asyncio
import random
import requests
import pymongo
from bson.objectid import ObjectId

# discord bot permissions

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
client = discord.Client(intents=intents)

mute_list = []

# insert tokens and database info here

discord_token = ''
mongouser = ''
mongopw = ''
mongodb = ''

# text prefix for commands

prefix = 'b'

#connect to mongoDB
db_client = pymongo.MongoClient("mongodb+srv://" + mongouser + ":" + mongopw + "@cluster0.thott.mongodb.net/" + mongodb + "?retryWrites=true&w=majority")
db = db_client.bettingDB
db_pokemon = db.pokemon
db_points = db.points

# class for bet object containing two sides and list of betters
class Bet:

    def __init__(self, side1: str, side2: str, betters1: dict, betters2: dict, open: bool):
        self.side1 = side1
        self.side2 = side2
        self.betters1 = betters1
        self.betters2 = betters2
        self.open = open

    # adds user to selected side of betters
    def add_better(self, side: str, user):
        if not self.open:
            return 'No bet is open'
        elif self.check_better(user.name):
            return 'User already entered bet'
        elif side == self.side1:
            self.betters1[user.name] = 0
            return str(user.name) + ' entered into bet for side: ' + side
        elif side == self.side2:
            self.betters2[user.name] = 0
            return str(user.name) + ' entered into bet for side: ' + side
        else:
            return "Side doesn't exist"

    # adds points to bet amount for user
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

    # check if user is in list of betters
    def check_better(self, user):
        if user in self.betters1 or user in self.betters2:
            return True
        else:
            return False

    # closes bet by deciding winner and distributes points, returns betters and their payouts
    def end_bet(self, side):
        response = ''
        print(self.betters1, self.betters2)
        if not self.open:
            return 'No bet is open'

        if side == self.side1:
            for user in self.betters1:
                change_points(self.betters1[user], user)
                response += user + ': +' + str(self.betters1[user]) + '\n'
            for user in self.betters2:
                change_points(-self.betters2[user], user)
                response += user + ': -' + str(self.betters2[user]) + '\n'
            self.open = False
            return 'Winner: ' + self.side1 + '\n' + response

        elif side == self.side2:
            for user in self.betters2:
                change_points(self.betters2[user], user)
                response += user + ': +' + str(self.betters2[user]) + '\n'
            for user in self.betters1:
                change_points(-self.betters1[user], user)
                response += user + ': -' + str(self.betters1[user]) + '\n'
            self.open = False
            return 'Winner: ' + self.side2 + '\n' + response

        else:
            return "Side doesn't exist"

    # returns side of bet that a user is currently in
    def send_side_from_user(self, user):
        if user in self.betters1:
            return self.side1
        elif user in self.betters2:
            return self.side2
        else:
            return None


# class for pokemon object with
class Pokemon:

    def __init__(self, name: str, user: str, picture: str, level: int, exp: int):
        self.name = name
        self.user = user
        self.picture = picture
        self.level = level
        self.exp = exp

    # adds experience points to pokemon
    def add_exp(self, exp: int, id: str):
        print(self.exp, exp)
        self.exp += exp
        response = str(exp) + ' experience has been given to ' + self.name + '. '
        response += self.level_check()
        update_pokemon_data(self.user, id, self)
        return response

    # evolves pokemon if able
    def evolve(self, user, id):
        species = requests.get('https://pokeapi.co/api/v2/pokemon-species/' + self.name).json()
        evolution_chain = requests.get(species['evolution_chain']['url']).json()

        # if try statement fails, then the pokemon has no evolution chain
        try:
            if evolution_chain['chain']['species']['name'] == self.name and evolution_chain['chain'][
                'evolves_to'] != []:
                if evolution_chain['chain']['evolves_to'][0]['evolution_details'][0]['min_level'] <= self.level:
                    print('evolve1')
                    new_name = evolution_chain['chain']['evolves_to'][0]['species']['name']
                    new_data = requests.get('https://pokeapi.co/api/v2/pokemon/' + new_name).json()
                    new_picture = new_data['sprites']['other']['official-artwork']['front_default']
                    new_pokemon = Pokemon(new_name, user, new_picture, self.level, self.exp)
                    update_pokemon_data(user, id, new_pokemon)
                    return 'Your ' + self.name.capitalize() + ' has evolved into ' + new_name.capitalize() + '!'
                else:
                    return 'Your pokemon cannot evolve'

            elif evolution_chain['chain']['evolves_to'][0]['species']['name'] == self.name and \
                    evolution_chain['chain']['evolves_to'][0]['evolves_to']:
                if evolution_chain['chain']['evolves_to'][0]['evolves_to'][0]['evolution_details'][0][
                    'min_level'] <= self.level:
                    print('evolve2')
                    new_name = evolution_chain['chain']['evolves_to'][0]['evolves_to'][0]['species']['name']
                    new_data = requests.get('https://pokeapi.co/api/v2/pokemon/' + new_name).json()
                    new_picture = new_data['sprites']['other']['official-artwork']['front_default']
                    new_pokemon = Pokemon(new_name, user, new_picture, self.level, self.exp)
                    update_pokemon_data(user, id, new_pokemon)
                    return 'Your ' + self.name.capitalize() + ' has evolved into ' + new_name.capitalize() + '!'
                else:
                    return 'Your pokemon cannot evolve'

            else:
                return 'Your pokemon cannot evolve'
        except:
            return 'Your pokemon cannot evolve'


    # exchanges pokemon for server points
    def exchange_for_points(self, user, id):
        user_info = db.points.find_one({'name': user})
        db_points.update_one({'name': user}, {'$set': {'name': user, 'points': user_info['points'] + self.exp}})
        db_pokemon.delete_one({'user': user, '_id': ObjectId(id)})
        return 'Your ' + self.name.capitalize() + ' has been converted into ' + str(self.exp) + ' points'

    # checks if pokemon has enough experience to level up
    def level_check(self):
        checking = True
        leveled_up = False
        species = requests.get('https://pokeapi.co/api/v2/pokemon-species/' + self.name).json()
        growth_rate = requests.get(species['growth_rate']['url']).json()
        found_index = -1

        for index, dic in enumerate(growth_rate['levels']):
            if dic['level'] == self.level + 1:
                found_index = index
                break

        while checking:
            if growth_rate['levels'][found_index]['experience'] <= self.exp:
                self.level += 1
                found_index += 1
                leveled_up = True
            else:
                checking = False

        if leveled_up:
            return 'Your ' + self.name + ' is now level ' + str(self.level)
        else:
            return ''



# creates ongoing bet object to be used for all bets
bet = Bet('', '', {}, {}, False)


# message for when bot is ready
@client.event
async def on_ready():
    print('We have logged in as {0,user}'.format(client))


# bot waits for messages in discord channel
@client.event
async def on_message(message):
    # bot ignores own messages
    if message.author == client.user:
        return

    # adds user to betting list
    if message.content.startswith(prefix + 'start'):
        response = add_user(message.author.name)
        await message.channel.send(response)

    # sends user's current balance
    if message.content.startswith(prefix + 'balance'):
        response = get_balance(message.author.name)
        await message.channel.send(response)

    # open a bet with two sides based on user replies
    if message.content.startswith(prefix + 'open'):

        global bet

        if bet.open:
            await message.channel.send("Another bet is still open")
            return

        await message.channel.send("Send name for first side")

        def check(reply):
            return reply.content.startswith(prefix)

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
                await message.channel.send(
                    "Second bet added. Bet open for " + side1.content[1:] + " and " + side2.content[1:])
                open_bet(side1.content[1:], side2.content[1:])

    # allow users to join an ongoing bet
    if message.content.startswith(prefix + 'join'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return

        await message.channel.send(
            "Which side are you joining?\nSide 1: " + bet.side1 + '\nSide 2: ' + bet.side2)

        def check(reply):
            return reply.content.startswith(prefix)

        try:
            reply = await client.wait_for('message', check=check, timeout=60.0)
            if reply.content != prefix + '1' and reply.content != prefix + '2':
                raise Exception("Only 1 or 2")
            else:
                if reply.content.startswith(prefix + '1'):
                    side = bet.side1
                elif reply.content.startswith(prefix + '2'):
                    side = bet.side2
                response = join_bet(side, message.author)

        except asyncio.TimeoutError:
            await message.channel.send('Timeout')

        except:
            await message.channel.send('Something broke')

        else:
            await message.channel.send(response)

    # allows users to add points to ongoing bet that they have already joined
    if message.content.startswith(prefix + 'add '):
        if not bet.open:
            await message.channel.send("No bet is open")
            return

        if not check_user(message.author.name):
            await message.channel.send('You are not in the system. Please use $start')
            return

        if get_side_from_user(message.author.name) == None:
            await message.channel.send("You are not in the bet")
            return

        amount = message.content[5:]

        try:
            amount = int(amount)

        except:
            await message.channel.send('Please enter only numbers')
            return

        points = db_points.find_one({'name': message.author.name})['points']

        try:
            print(type(amount))
            side = get_side_from_user(message.author.name)
            if amount < 0:
                await message.channel.send("Put a positive number")
                return
            if side == bet.side1:
                if amount + bet.betters1[message.author.name] > points:
                    await message.channel.send("You do not have this many points")
                    return
            elif side == bet.side2:
                if amount + bet.betters2[message.author.name] > points:
                    await message.channel.send("You do not have this many points")
                    return
            response = add_bet(side, message.author.name, str(amount))

        except:

            await message.channel.send('Something broke')

        else:
            await message.channel.send(response)

    # closes ongoing bet and distributes points to betters
    if message.content.startswith(prefix + 'close'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return

        await message.channel.send("Which side won?\nSide 1: " + bet.side1 + '\nSide 2: ' + bet.side2)

        def check(reply):
            return reply.content.startswith(prefix)

        try:
            reply = await client.wait_for('message', check=check, timeout=60.0)
            if reply.content != prefix + '1' and reply.content != prefix + '2':
                raise Exception("Only 1 or 2")
            else:
                if reply.content.startswith(prefix + '1'):
                    side = bet.side1
                elif reply.content.startswith(prefix + '2'):
                    side = bet.side2
                response = close_bet(side)

        except asyncio.TimeoutError:
            await message.channel.send('Timeout')

        except:
            await message.channel.send('Something broke')

        else:
            await message.channel.send(response)

    # gives user 1000 points if they have zero
    if message.content.startswith(prefix + 'beg'):
        if not check_user(message.author.name):
            await message.channel.send('You are not in the system. Please use $start')
            return

        if db_points.find_one({'name': message.author.name})['points'] <= 0:
            change_points(1000, message.author.name)
            await message.channel.send(message.author.name + ' has been given 1000 points')
        else:
            await message.channel.send(message.author.name + ' still has points')


    # pay points to server mute user for one minute and remute if they attempt to unmute
    if message.content.startswith(prefix + 'mute'):
        if not check_user(message.author.name):
            await message.channel.send('You are not in the system. Please use $start')
            return

        if not check_points(1000, message.author.name):
            await message.channel.send('You do not have enough points')
            return
        else:
            await message.channel.send("Who are you muting? This will cost 1000 points")

            def check(reply):
                return reply.content.startswith(prefix)

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
                    await asyncio.sleep(30)
                    mute_list.remove(user)
                    await user.edit(mute=False)
                    await message.channel.send(user.name + ' has been unmuted')

    # returns sides of open bet
    if message.content.startswith(prefix + 'check'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return
        else:
            await message.channel.send('Side 1: ' + bet.side1 + '\n' + 'Side 2: ' + bet.side2)

    # returns list of betters with their current bet
    if message.content.startswith(prefix + 'betters'):
        if not bet.open:
            await message.channel.send("No bet is open")
            return
        else:
            response = get_betters()
            await message.channel.send(response)

    # rolls gacha system
    if message.content.startswith(prefix + 'gacha'):
        if not check_user(message.author.name):
            await message.channel.send('You are not in the system. Please use $start')
            return
        if check_points(1000, message.author.name):
            pokemon = roll_gacha(message.author.name)
            roll_response = pokemon.name.capitalize() + '\n' + 'Level: ' + str(pokemon.level) + '\n' + 'Exp: ' + str(
                pokemon.exp)
            await message.channel.send(roll_response)
            await message.channel.send(pokemon.picture)
            change_points(-1000, message.author.name)
            add_response = add_pokemon(pokemon)
            await message.channel.send(add_response)
        else:
            await message.channel.send('You do not have enough points')


    # shows user's pokemon collection
    if message.content.startswith(prefix + 'collection'):

        collection = db_pokemon.find({'user': message.author.name})

        response = ''
        for info in collection:
            response += info['name'].capitalize() + '- Level: ' + str(info['level']) + ', Exp: ' + str(info['exp']) + ', Id: ' + str(info['_id']) + '\n'
        await message.channel.send(response)

    # attempts to evolve pokemon
    if message.content.startswith(prefix + 'evolve '):

        id = message.content[8:]

        if not find_pokemon(message.author.name, id):
            await message.channel.send('You do not have that pokemon in your collection')
            return

        else:
            pokemon = get_pokemon_data(message.author.name, id)
            response = pokemon.evolve(message.author.name, id)
            await message.channel.send(response)

    # converts user points to experience for pokemon
    if message.content.startswith(prefix + 'exp '):

        id = message.content[5:]

        if not find_pokemon(message.author.name, id):
            await message.channel.send('You do not have that pokemon in your collection')
            return

        else:
            await message.channel.send("How much exp are you giving? Please enter a number.")

            def check(reply):
                return reply.content.startswith(prefix)

            try:
                reply = await client.wait_for('message', check=check, timeout=60.0)
                if not check_points(int(reply.content[1:]), message.author.name):
                    await message.channel.send('You do not have that many points')
                    return

            except asyncio.TimeoutError:
                await message.channel.send('Timeout')

            except:
                await message.channel.send('Something broke')

            else:
                pokemon = get_pokemon_data(message.author.name, id)
                response = pokemon.add_exp(int(reply.content[1:]), id)
                await message.channel.send(response)

    # converts pokemon experience to points and deletes pokemon
    if message.content.startswith(prefix + 'melt '):

        id = message.content[6:]

        if not find_pokemon(message.author.name, id):
            await message.channel.send('You do not have that pokemon in your collection')
            return

        else:
            pokemon = get_pokemon_data(message.author.name, id)
            response = pokemon.exchange_for_points(message.author.name, id)
            await message.channel.send(response)

    # help command for list of message commands
    if message.content.startswith(prefix + 'help'):
        help_message = '''Command List:
        start: Initialize user into betting system
        balance: View your own balance of points
        open: Opens a bet if none is open
        join: Enter yourself into the open bet
        add {number}: Add points into joined bet
        check: Displays bet info
        betters: Lists users that have entered bet
        close: End open bet and choose winners
        beg: Get points if you have none left
        prizes: Display list of prizes to exchange with points
        collection: View pokemon collection

        Warning: Multiple users sending commands will overlap each other. One user should enter commands at a time.'''
        await message.channel.send(help_message)

    # lists prizes that can be bought with points
    if message.content.startswith(prefix + 'prizes'):
        prize_message = '''Prize Commands:
        mute: Mute a user in a voice channel for a minute (1000)
        gacha: Do a roll in the gacha (1000)
        exp {pokemon name}: Convert your points into experience for your pokemon
        evolve {pokemon name}: Evolve your pokemon if the conditions are met
        melt {pokemon name}: Delete and convert your pokemon's exp to points
        '''
        await message.channel.send(prize_message)


# bot waits for changes in voice state of members in discord call
@client.event
async def on_voice_state_update(member, before, after):
    # remutes server muted member if they attempt to unmute
    if member in mute_list:
        if before.mute == True and after.mute == False:
            await member.edit(mute=True)

# add points to bet for user
def add_bet(side, user, amount):
    global bet
    output = bet.add_bet(side, user, amount)
    return output


# initializes user into betting list by adding to json file and giving initial points
def add_user(user):
    if not check_user(user):
        db_points.insert_one({'name': user, 'points': 1000})
        return user + ' has been entered into system'
    else:
        return user + ' already exists in system'


# obtains balance from user data
def get_balance(user):
    user_data = db_points.find_one({'name': user})
    if user_data == None:
        return 'User does not exist'
    else:
        return user + "'s balance is " + str(user_data['points'])


# obtains name of side that user is in
def get_side_from_user(user):
    global bet
    output = bet.send_side_from_user(user)
    return output


# adds user to list of betters
def join_bet(side, user):
    global bet
    output = bet.add_better(side, user)
    return output


# opens bet with two sides
def open_bet(side1, side2):
    global bet
    bet = Bet(side1, side2, {}, {}, True)


# closes bet and distributes points
def close_bet(side):
    global bet
    output = bet.end_bet(side)
    return output


# updates user data in database
def write_point_data(user, amount):
    db_info = db_points.find_one({'name': user})
    print(db_info)
    #db_points.update_one({'name': user, 'points': })


# changes amount of points that a user has and updates txt file
def change_points(amount, user):
    print(amount, user)
    user_data = db_points.find_one({'name': user})
    print(user_data)
    if user_data == None:
        return 'User does not exist'
    else:
        db_points.update_one({'name': user}, {'$set': {'name': user, 'points': user_data['points'] + amount}})
        return user + "'s points changed by " + str(amount)


# check if user has enough points for commands
def check_points(amount, user):
    user_data = db_points.find_one({'name': user})
    if user_data['points'] >= amount:
        return True
    else:
        return False


# check if user is in database system
def check_user(user):
    if db_points.find_one({'name': user}) == None:
        return False
    else:
        return True


# gets list of betters and their current bets for open bet
def get_betters():
    response = ''
    if bet.betters1 == {} and bet.betters2 == {}:
        return 'There are no betters'
    response += bet.side1 + ':\n'
    for better in bet.betters1:
        response += better + ': ' + str(bet.betters1[better]) + '\n'
    response += bet.side2 + ':\n'
    for better in bet.betters2:
        response += better + ': ' + str(bet.betters2[better]) + '\n'
    return response


# rolls gacha system
def roll_gacha(user):
    number = random.randrange(1, 899)
    level = random.randrange(5, 31)
    pokemon_data = requests.get('https://pokeapi.co/api/v2/pokemon/' + str(number)).json()
    species = requests.get('https://pokeapi.co/api/v2/pokemon-species/' + str(number)).json()
    growth_rate = requests.get(species['growth_rate']['url']).json()
    exp = growth_rate['levels'][level - 1]['experience']
    pokemon = Pokemon(pokemon_data['name'], user, pokemon_data['sprites']['other']['official-artwork']['front_default'],
                      level, exp)
    return pokemon


# adds pokemon into data file for user's collection
def add_pokemon(pokemon: Pokemon):

    dict = {'name': pokemon.name, 'user': pokemon.user, 'picture': pokemon.picture, 'level': pokemon.level, 'exp': pokemon.exp}
    db_pokemon.insert_one(dict)
    return pokemon.name.capitalize() + ' added to ' + pokemon.user + "'s collection"


# find if pokemon exists in user's collection and returns location in data
def find_pokemon(user, id):
    if db_pokemon.find_one({'user': user, '_id': ObjectId(id)}):
        return True
    else:
        return False


# returns pokemon object from data found at a given index
def get_pokemon_data(user, id):
    info = db_pokemon.find_one({'user': user, '_id': ObjectId(id)})
    pokemon = Pokemon(info['name'], info['user'], info['picture'], info['level'], info['exp'])
    return pokemon


# updates data for pokemon in user's collection
def update_pokemon_data(user, id, pokemon: Pokemon):
    new_data = {'name': pokemon.name, 'user': pokemon.user, 'picture': pokemon.picture, 'level': pokemon.level, 'exp': pokemon.exp}
    db_pokemon.update_one({'user': user, '_id': ObjectId(id)}, {'$set': new_data})


client.run(discord_token)
