#app/discord/policies.py
import functools

from app.discord.dependencies import user_service_ctx
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
            try:
                async with user_service_ctx() as user_service:
                    user = await user_service.get_user_by_discord(inter.author.id)
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
        async def wrapper(self, inter, *args, **kwargs):
            try:
                async with user_service_ctx() as user_service:
                    user = await user_service.get_user_by_discord(inter.author.id)
            except NotFoundError:
                raise InvalidToken()
            check_function(user)
            return await func(self, inter, *args, **kwargs)
        return wrapper
    return decorator