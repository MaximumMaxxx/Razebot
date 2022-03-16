# This file holds all the environment variables
# Technically secrets isn't the correct word but it's a good enough descriptor
import time


class Secrets():
    def __init__(self) -> None:
        pass

    bottoken = ""
    dscclientid = ""
    dscclientsecret = ""
    dscredirecturi = ""

    dbuname = ""
    dbpassword = ""
    database = ""
    dbhost = ""

    websecretkey = b""
    webhost = ""
    webport = 6969
