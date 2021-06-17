# Discord Betting Bot

## Description
 Discord bot that allows users to create bets for points that can be exchanged for server prizes. Prizes include server actions interacting with users or trading cards created using PokeApi. Bot data is stored in a AWS database using MondoDB with NoSQL.
 
## How to use
 The code requires Python 3 which can be downloaded from https://www.python.org/downloads/. bettingBot.py contains the code for all bot functionality. Creating a Discord bot using the code can be done at https://discord.com/developers/applications. Create a bot using "New Application" and navigating to the "Bot" settings. Upon creation, the bot will have a token that must be placed into bettingBot.py in the discord_token variable in line 19. 
 The bot also requires MongoDB Community Server which can be downloaded from https://www.mongodb.com/try/download/community. Create a user and password to access the desired storage cluster in your database. The user, password, and database name must be inserted into bettingBot.py at line 20. Run the python script and invite the bot into a Discord server to start using the bot. The default text command for help instructions is "bhelp".
 
 ## Dependencies
  The bot requires the following Python libraries: discord, asyncio, random, requests, pymongo, bson. These libraries already exist in the virtual environment folder, \venv\, but will require downloading if using an outside environment.
