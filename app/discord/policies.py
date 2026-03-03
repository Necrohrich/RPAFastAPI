#app/discord/policies.py
import functools

from app.discord.dependencies import get_auth_service
from app.exceptions.auth_exceptions import InvalidToken
from app.exceptions.common_exceptions import NotFoundError


def discord_policy():
    """
    Используется как @discord_policy()
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, inter, *args, **kwargs):

            auth_service = await get_auth_service()

            discord_id = inter.author.id

            try:
                user = await auth_service.get_user_by_discord(discord_id)
            except NotFoundError:
                raise InvalidToken()

            return await func(self, inter, user, *args, **kwargs)

        return wrapper
    return decorator


def require_role(check_function):
    """
    Используется как @require_role(PlatformPolicies.require_superadmin)
    :param check_function:
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, inter, user, *args, **kwargs):

            check_function(user)

            return await func(self, inter, user, *args, **kwargs)

        return wrapper
    return decorator