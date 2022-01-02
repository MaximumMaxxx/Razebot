<p align="center">
    <a href="https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true">
        <img src="assets/Valobot logo raze thicckened.png" alt="Logo" width="160" height="160">
    </a>
<h5 align="center"> Razebot</h5>
</p>

<h3>Notice</h3>
This bot requires Python 3.4+ to function. This is due to Discord.py. 
Additionally it'll probably work on Windows but I can't guarentee it.

<h3>Features</h3>

- Automatic role assignment
- Fully integrated rank checking
- Saves all user data to SQL database
- Dynamic embeds

Rank check example

![Rank Checking](https://github.com/MaximumMaxxx/Razebot/blob/main/assets/razebot%20sample.png?raw=true)

<h3>Hosting guide</h3>

For this guide I'll assume you have atleast a basic understanding of how to use python and the command line

1.) Either download the latest zip file from the releases tab or run a git clone with ```git clone https://github.com/MaximumMaxxx/Razebot/tree/Web``` in whatever folder you want the bot to live


2.) cd into the folder that was just created and run ```python3 -m venv env``` and ```source env/bin/activate``` or ```env/Scripts\activate.bat``` on Unix/Linux or Windows respectively.

3.) run ```python3 -m pip install -r requirements.txt``` your terminal will now be flooded with messages. If you want to modify the website it is also a good idea to run ```npm install``` to install tailwindcss. Tailwind can be run with ```npx tailwindcss --watch --output ./static/css/main.css``` which will watch from any changes in the templates folder and rebuild the css.

3.25) Install pycord with ```pip install git+https://github.com/Pycord-Development/pycord```

3.5) Setup a Mysql server [Here is the official guide](https://dev.mysql.com/doc/mysql-getting-started/en/)

4.) Go into ```secrets.py``` and add in all the fields. These are required for the bot the be run. This file should never leave your compute or be commited to somewhere like Github.

5.) Finally run ```python3 app.py``` to start the bot and web server.

6.) if you get an error in ```discord/compat.py``` go into that file and change create_task = asyncio.async

<h3>Credit to all the projects I took from for this</h3>

[Player data from: unoffical valorant api by Henrick-3](https://github.com/Henrik-3/unofficial-valorant-api)

[Images and icons mostly from: Valorant-api.com](https://dash.valorant-api.com)

[Inspirtation and guidence: Valorant Rank Yoinker](https://github.com/isaacKenyon/VALORANT-rank-yoinker)

Also a bunch of articles and stack overflow helps.

Additionally I can't deny that [Valorant Labs](https://top.gg/bot/702201518329430117) was here before me and has some more features. 

<h3>All the people who helped</h3>

Lacas - convincing me to multi-server the bot

Danika - Emotional support

Yang Yang - Suggesting features

Rogue - testing and some dev help


Avery - Initially teaching me to do SQL stuff

And everyone else in the Valorant Club discord

<h3>Legal Stuff</h3>

THIS PROJECT IS NOT ASSOCIATED OR ENDORSED BY RIOT GAMES. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
