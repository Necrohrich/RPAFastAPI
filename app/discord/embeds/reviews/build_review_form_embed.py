# app/discord/embeds/reviews/build_review_form_embed.py
import disnake
from uuid import UUID

from app.domain.enums.review_rating_enum import ReviewRatingEnum
from app.dto.game_review_dtos import GameReviewResponseDTO

_RATING_LABELS: dict[ReviewRatingEnum, str] = {
    ReviewRatingEnum.TERRIBLE:  "😡 Плохо",
    ReviewRatingEnum.BAD:       "😕 Есть осадок",
    ReviewRatingEnum.NEUTRAL:   "😐 Нейтрально",
    ReviewRatingEnum.GOOD:      "🙂 Хорошо",
    ReviewRatingEnum.EXCELLENT: "🤩 Превосходно",
}

_MAX_DISPLAY_LEN = 40


def _truncate(text: str, max_len: int = _MAX_DISPLAY_LEN) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def build_review_form_embed(
    review: GameReviewResponseDTO,
    attending_players: list[tuple[UUID, str]] | None = None,
) -> disnake.Embed:
    """
    Embed для формы заполнения отзыва.

    attending_players — список (user_id, login) присутствовавших игроков.
    Используется для отображения логина лучшего игрока вместо UUID/mention.
    """
    embed = disnake.Embed(
        title="📋 Ваш отзыв",
        color=disnake.Color.blurple(),
    )

    # Оценка
    rating_text = (
        _RATING_LABELS.get(review.rating, "не указана")
        if review.rating
        else "❓ не указана"
    )
    embed.add_field(name="⭐ Оценка", value=rating_text, inline=False)

    # Комментарий
    comment_text = (
        _truncate(review.comment) if review.comment and review.comment.strip()
        else "✏️ не написан"
    )
    embed.add_field(name="💬 Комментарий", value=comment_text, inline=False)

    # Лучшие сцены
    if review.best_scenes:
        scenes_lines = [
            f"• {_truncate(name, 30)} — {stype}"
            for name, stype in list(review.best_scenes.items())[:5]
        ]
        if len(review.best_scenes) > 5:
            scenes_lines.append(f"…и ещё {len(review.best_scenes) - 5}")
        embed.add_field(
            name="🎬 Лучшие сцены",
            value="\n".join(scenes_lines),
            inline=False,
        )
    else:
        embed.add_field(name="🎬 Лучшие сцены", value="не выбраны", inline=False)

    # Лучшие НИП
    if review.best_npc:
        npc_lines = [f"• {_truncate(n, 30)}" for n in review.best_npc[:5]]
        if len(review.best_npc) > 5:
            npc_lines.append(f"…и ещё {len(review.best_npc) - 5}")
        embed.add_field(
            name="🧙 Лучшие НИП",
            value="\n".join(npc_lines),
            inline=False,
        )
    else:
        embed.add_field(name="🧙 Лучшие НИП", value="не выбраны", inline=False)

    # Лучший игрок — показываем логин из attending_players если доступен
    best_player_text = "не выбран"
    if review.best_player_id:
        # Ищем логин в переданном списке attending_players
        login: str | None = None
        if attending_players:
            login = next(
                (l for uid, l in attending_players if uid == review.best_player_id),
                None,
            )
        best_player_text = login if login else f"`{review.best_player_id}`"

    embed.add_field(name="🏆 Игрок сессии", value=best_player_text, inline=False)

    embed.set_footer(text="Обязательно: оценка и комментарий. Остальное — по желанию.")
    return embed