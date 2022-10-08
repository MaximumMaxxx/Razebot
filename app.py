# Code slightly stolen from here: https://replit.com/@cooljames1610/economybot I still modified it a bunch but the bot to app communication is not me
from os import environ
import logging

from blueprints.api import blueprint as api_blueprint
from blueprints.web import blueprint as web_blueprint
from lib.globals import app, bot

# Configure logging
logging.basicConfig(level=logging.INFO, filename="Logs.log")

# Load in the pages
app.register_blueprint(api_blueprint, url_prefix="/api")
app.register_blueprint(web_blueprint, url_prefix="/")

# Load in a bunch of config stuff
app.secret_key = environ.get('websecretkey')
app.config["DISCORD_CLIENT_ID"] = environ.get('dscclientid')
app.config["DISCORD_CLIENT_SECRET"] = environ.get('dscclientsecret')
app.config["DISCORD_REDIRECT_URI"] = environ.get('dscredirecturi')
app.config["DISCORD_BOT_TOKEN"] = environ.get('bottoken')

# Remove this when going into production
environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"


Globalextensions = [
    "bot.accManagement",
    "bot.listeners",
    "bot.other",
    "bot.rankCheck"
]


def run():  # Credit to Muffin's Dev#6537 for some of this code
    bot.loop.create_task(
        app.run_task(
            host=environ.get('webhost'),
            port=environ.get('webport'),
            debug=True
        )
    )

    # Load in all the extensions
    for extension in Globalextensions:
        try:
            bot.load_extension(extension)
        except Exception as error:
            print(
                f'{extension} failed to load [{error}]'
            )
            logging.error(
                f"{extension} failed to load [{error}]"
            )
    bot.run(
        environ.get('bottoken')
    )


if __name__ == "__main__":
    run()
