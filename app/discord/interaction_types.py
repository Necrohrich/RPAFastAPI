# app/discord/interaction_types.py
from disnake import ApplicationCommandInteraction
from app.dto.auth_dtos import UserDTO

class PolicyInteraction(ApplicationCommandInteraction):
    user_data: UserDTO