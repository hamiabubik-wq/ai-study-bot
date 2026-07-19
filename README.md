# Study AI Bot Full

Функции: админ-панель, 7 запросов в день, бессрочный Premium, история, голос, анализ изображений, помощник программиста, документы и поиск в интернете.

## Запуск

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Скопируй `.env.example` в `.env`, заполни токены и запусти:

```bash
python main.py
```

## Админ

- `/admin`
- `/grant TELEGRAM_ID`
- `/revoke TELEGRAM_ID`
- `/user TELEGRAM_ID`
- `/myid`

Друг должен сначала нажать `/start`.

## Railway

Добавь переменные из `.env.example`. Для сохранения SQLite между деплоями подключи Volume к `/data` и поставь `DATABASE_PATH=/data/bot.db`.
