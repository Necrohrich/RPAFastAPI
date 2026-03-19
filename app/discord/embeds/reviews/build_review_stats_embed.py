# app/discord/embeds/reviews/build_review_stats_embed.py
import disnake

from app.dto.game_review_dtos import (
    NpcStatDTO,
    SceneStatDTO,
    PlayerStatDTO,
    GameReviewRatingStatsDTO,
)

_RATING_LABELS_RU: dict[str, str] = {
    "terrible": "😡 Плохо",
    "bad":      "😕 Есть осадок",
    "neutral":  "😐 Нейтрально",
    "good":     "🙂 Хорошо",
    "excellent": "🤩 Превосходно",
}


def build_npc_stats_embed(
    game_name: str,
    stats: list[NpcStatDTO],
) -> disnake.Embed:
    embed = disnake.Embed(
        title=f"🧙 Топ НИП — {game_name}",
        color=disnake.Color.purple(),
    )
    if not stats:
        embed.description = "Нет данных."
        return embed
    lines = [f"`{i + 1}.` **{s.name}** — {s.count} упоминаний" for i, s in enumerate(stats[:20])]
    embed.description = "\n".join(lines)
    return embed


def build_scenes_stats_embed(
    game_name: str,
    stats: list[SceneStatDTO],
) -> disnake.Embed:
    embed = disnake.Embed(
        title=f"🎬 Топ сцен — {game_name}",
        color=disnake.Color.orange(),
    )
    if not stats:
        embed.description = "Нет данных."
        return embed
    lines = [
        f"`{i + 1}.` **{s.name}** ({s.scene_type}) — {s.count} упоминаний"
        for i, s in enumerate(stats[:20])
    ]
    embed.description = "\n".join(lines)
    return embed


def build_players_stats_embed(
    game_name: str,
    stats: list[PlayerStatDTO],
) -> disnake.Embed:
    embed = disnake.Embed(
        title=f"🏆 Топ игроков — {game_name}",
        color=disnake.Color.gold(),
    )
    if not stats:
        embed.description = "Нет данных."
        return embed
    lines = [
        f"`{i + 1}.` <@{s.user_id}> — {s.count} упоминаний"
        for i, s in enumerate(stats[:20])
    ]
    embed.description = "\n".join(lines)
    return embed


def build_rating_stats_embed(
    game_name: str,
    stats: GameReviewRatingStatsDTO,
) -> disnake.Embed:
    label_ru = _RATING_LABELS_RU.get(stats.label.lower() if stats.label else "", stats.label)
    embed = disnake.Embed(
        title=f"⭐ Оценка игры — {game_name}",
        color=disnake.Color.blurple(),
    )
    embed.add_field(name="Итоговая оценка", value=label_ru, inline=False)
    embed.add_field(
        name="Взвешенный балл",
        value=f"{stats.weighted_score:.2f} / 4.00",
        inline=True,
    )
    embed.add_field(name="Всего отзывов", value=str(stats.total_reviews), inline=True)
    embed.add_field(name="Уникальных авторов", value=str(stats.total_reviewers), inline=True)
    embed.add_field(name="Охваченных сессий", value=str(stats.total_sessions), inline=True)
    embed.set_footer(
        text="Оценка учитывает число активных игроков и частоту написания отзывов."
    )
    return embed