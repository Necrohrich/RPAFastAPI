# app/discord/embeds/reviews/build_review_publish_embed.py
import disnake

from app.domain.enums.review_anonymity_enum import ReviewAnonymityEnum
from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.dto.game_review_dtos import GameReviewResponseDTO

_RATING_LABELS: dict[ReviewRatingEnum, str] = {
    ReviewRatingEnum.TERRIBLE: "😡 Плохо",
    ReviewRatingEnum.BAD:      "😕 Есть осадок",
    ReviewRatingEnum.NEUTRAL:  "😐 Нейтрально",
    ReviewRatingEnum.GOOD:     "🙂 Хорошо",
    ReviewRatingEnum.EXCELLENT: "🤩 Превосходно",
}


def build_review_publish_embed(
    review: GameReviewResponseDTO,
    session_number: int,
    game_name: str,
    author_discord_id: int | None = None,
    best_player_login: str | None = None,
) -> disnake.Embed:
    """
    Embed для публикации отзыва в канал.

    Для анонимных отзывов автор не указывается.
    best_player_login — логин лучшего игрока (если известен), иначе mention по UUID.
    """
    is_anonymous = review.anonymity == ReviewAnonymityEnum.PRIVATE

    title = f"📝 Отзыв на сессию #{session_number} — {game_name}"
    embed = disnake.Embed(title=title, color=disnake.Color.blurple())

    # footer с UUID отзыва — полезен для slash-команд управления
    embed.set_footer(text=f"review_id: {review.id}")

    # Автор
    if is_anonymous or not author_discord_id:
        embed.add_field(name="👤 Автор", value="🎭 Анонимно", inline=True)
    else:
        embed.add_field(name="👤 Автор", value=f"<@{author_discord_id}>", inline=True)

    # Оценка
    rating_text = _RATING_LABELS.get(review.rating, "—") if review.rating else "—"
    embed.add_field(name="⭐ Оценка", value=rating_text, inline=True)

    # Комментарий
    if review.comment and review.comment.strip():
        embed.add_field(name="💬 Комментарий", value=review.comment[:1000], inline=False)

    # Лучшие сцены
    if review.best_scenes:
        scenes_text = "\n".join(
            f"• {name} — {stype}" for name, stype in review.best_scenes.items()
        )
        embed.add_field(name="🎬 Лучшие сцены", value=scenes_text[:500], inline=False)

    # Лучшие НИП
    if review.best_npc:
        embed.add_field(
            name="🧙 Запомнившиеся НИП",
            value=", ".join(review.best_npc)[:500],
            inline=False,
        )

    # Лучший игрок — предпочитаем логин, fallback на mention/UUID
    if review.best_player_id:
        if best_player_login:
            player_text = f"**{best_player_login}**"
        else:
            player_text = f"<@{review.best_player_id}>"
        embed.add_field(name="🏆 Игрок сессии", value=player_text, inline=False)

    return embed


def build_review_publish_stats_header(
    session_number: int,
    game_name: str,
    total: int,
) -> disnake.Embed:
    """Заголовочный embed перед пачкой опубликованных отзывов."""
    session_label = f"сессию #{session_number}" if session_number else "все сессии"
    return disnake.Embed(
        title=f"📊 Отзывы на {session_label} — {game_name}",
        description=f"Всего отзывов: **{total}**",
        color=disnake.Color.green(),
    )