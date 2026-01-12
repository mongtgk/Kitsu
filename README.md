![logo.png](logo.png)

# Kitsu

Открытый веб‑сервис для поиска и просмотра аниме. Текущий статус: MVP/предпродакшн-стабилизация. Авторитетный API реализован на FastAPI; фронтенд — Next.js. Исторический PocketBase **устарел и удалён из потока данных**.

## Архитектура

```
[Next.js фронтенд] --(REST/JSON)--> [FastAPI бэкенд] --(SQLAlchemy)--> [PostgreSQL]
        |
        +--(HiAnime скрейпер через Next API routes для источников воспроизведения)

[Загрузки/аватары] FastAPI раздаёт по /media/avatars c локальной ФС (без CDN)
```

Фронтенд API-first: без запущенного бэкенда данные не рендерятся, страницы пустые; первый целевой продакшн-деплой планируется на Render.

## Технологический стек

- Бэкенд: FastAPI, SQLAlchemy 2 (async), Alembic, PostgreSQL
- Фронтенд: Next.js 15 (app router), React 18, Tailwind, shadcn/ui, React Query, Axios
- Прочее: next-runtime-env, ArtPlayer + HLS.js, вспомогательные скрейперы HiAnime

## Структура репозитория

- `backend/` — FastAPI-сервис и миграции Alembic
- `src/` — код Next.js фронтенда
- `Dockerfile` — образ фронтенда
- `backend/Dockerfile` — образ бэкенда
- `backend/docker-compose.yml` — бэкенд + PostgreSQL для локалки
- `docker-compose.yml` — устаревший compose для фронтенда/прокси (без PocketBase)
- `docs/` — легаси-артефакты

## Запуск локально (обзор)

1. Бэкенд: подготовить `.env` (см. `backend/README.md`), поднять PostgreSQL, применить миграции Alembic, запустить `uvicorn app.main:app --reload` или `docker compose -f backend/docker-compose.yml up backend`.
2. Фронтенд: задать `NEXT_PUBLIC_API_BASE_URL` и `NEXT_PUBLIC_PROXY_URL`, выполнить `npm install`, затем `npm run dev`.

## Деплой на Render (обзор)

- Собрать отдельные образы фронтенда и бэкенда из соответствующих Dockerfile.
- Предоставить управляемый PostgreSQL, применить миграции до приёма трафика.
- Смонтировать постоянное хранилище для `backend/uploads/avatars`, иначе аватары теряются при перезапусках.
- Настроить переменные окружения согласно `backend/README.md` и `frontend/README.md`.
- Фронтенд должен ссылаться на публичный URL бэкенда (`NEXT_PUBLIC_API_BASE_URL`) и m3u8-прокси (`NEXT_PUBLIC_PROXY_URL`).

## Дополнительная документация

- [`backend/README.md`](backend/README.md)
- [`frontend/README.md`](frontend/README.md)
- [`ROADMAP.md`](ROADMAP.md)
