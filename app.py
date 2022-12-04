# Code slightly stolen from here: https://replit.com/@cooljames1610/economybot I still modified it a bunch but the bot to app communication is not me
from os import environ
import logging

from blueprints.api import blueprint as api_blueprint
from blueprints.web import blueprint as web_blueprint
from sqlalchemy import MetaData
from lib.globals import app, bot, engine
from lib.Helper import parseTrueFalse

# Configure logging
logging.basicConfig(level=logging.INFO, filename="Logs.log")

# Load in the pages
app.register_blueprint(api_blueprint, url_prefix="/api")
app.register_blueprint(web_blueprint, url_prefix="/")


Globalextensions = [
    "bot.accManagement",
    "bot.listeners",
    "bot.other",
    "bot.rankCheck"
]


def run():  # Credit to Muffin's Dev#6537 for some of this code

    print(f"Rnning with the webserver: {environ.get('runWebServer')}")
    # Check if they want to run the webserver
    # If they do, then create an async task and add it to the event loop
    if parseTrueFalse(environ.get("runWebServer")):
        bot.loop.create_task(
            app.run_task(
                host=environ.get('webhost'),
                port=environ.get('webport'),
                debug=True
            )
        )

    # Load in all the extensions
    print("Loading extensions")
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

    print("Starting bot, this may take a minute or two")
    bot.run(
        environ.get('bottoken')
    )


if __name__ == "__main__":
    run()
