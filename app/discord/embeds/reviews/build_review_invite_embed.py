# app/discord/embeds/reviews/build_review_invite_embed.py
import disnake

from app.dto import GameSessionResponseDTO


def build_review_invite_embed(
    session: GameSessionResponseDTO,
    game_name: str,
) -> disnake.Embed:
    """
    Главная страница приглашения к отзыву.

    Отображается в канале игры (или в личке) при завершении сессии.
    Содержит краткую инструкцию по заполнению отзыва.
    """
    embed = disnake.Embed(
        title=f"📝 Сессия #{session.session_number} завершена!",
        description=(
            f"**{game_name}** — сессия №{session.session_number}"
            f" «{session.title or '—'}» завершена.\n\n"
            "Хотите оставить отзыв?\n\n"
            "**Инструкция:**\n"
            "• Нажмите **✅ Оставить отзыв** — откроется форма заполнения.\n"
            "• Обязательно укажите **оценку** и **комментарий**.\n"
            "• Остальные поля (лучшие сцены, НИП, игрок) — по желанию.\n"
            "• Отправить можно **публично** или **анонимно**.\n"
            "• Нажмите **❌ В другой раз** — отзыв будет отменён.\n\n"
            "⏰ Время на заполнение ограничено."
        ),
        color=disnake.Color.blurple(),
    )
    if session.session_number:
        embed.set_footer(text=f"session_id:{session.id}|game:{game_name}")
    return embed