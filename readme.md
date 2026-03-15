## Alembic
alembic -c alembic.ini revision --autogenerate -m "добавить таблицу"

alembic -c alembic.ini upgrade head

alembic -c alembic.ini downgrade -1

## Ссылка для Discord-бота

```jupyterpython
import discord

# Читаем файл и прикрепляем к сообщению
file = discord.File("images/photo1.png", filename="photo1.png")

embed = discord.Embed(title="Заголовок")

# Ссылка на attachment:// + имя файла
embed.set_image(url="attachment://photo1.png")

await channel.send(file=file, embed=embed)
```

## Посмотреть структуру файла
cmd /c "tree /F /A | findstr /V cpython | findstr /V __pycache__"
