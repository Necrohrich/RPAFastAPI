# app/exceptions/user_exceptions.py

class LoginAlreadyExists(Exception):
    pass

class EmailAlreadyExists(Exception):
    pass

class DiscordAlreadyLinked(Exception):
    pass