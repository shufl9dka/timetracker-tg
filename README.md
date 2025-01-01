## Как запустить локально?

1. Создать файл `.env` в этом каталоге с таким содержимым:
```bash
POSTGRES_PASSWORD=pgpassword
REDIS_PASSWORD=rdpassword
REDIS_USER_PASSWORD=rduserpassword
REDIS_USER=rduser
BOT_TOKEN=12345678:ABCDEFG123123123123
FERNET_KEY=abacaba
```
`BOT_TOKEN` -- токен телеграм-бота из [@BotFather](https://t.me/BotFather)

2. Запустить компоуз: `docker-compose up --build`
