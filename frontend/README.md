# Фронтенд (Next.js)

## Назначение

Пользовательский веб-интерфейс для каталога аниме и воспроизведения через HLS-прокси. Получает данные из FastAPI-бэкенда; без доступного API интерфейс работает некорректно.

## Технологии

- Next.js 15 (app router), React 18
- Tailwind CSS, shadcn/ui
- React Query, Axios, zustand
- next-runtime-env для прокидывания переменных окружения в рантайме
- ArtPlayer + HLS.js для плеера

## Обязательные переменные окружения

- `NEXT_PUBLIC_API_BASE_URL` — публичный URL FastAPI (например, `http://localhost:8000`).
- `NEXT_PUBLIC_PROXY_URL` — URL HLS/m3u8-прокси для выдачи потоков (например, `http://localhost:4040`); нужен для проксирования m3u8/HLS запросов плеера с корректными заголовками и обходом CORS.

Укажите их в `.env.local` для локальной работы или в переменных окружения Render. При отсутствии `NEXT_PUBLIC_API_BASE_URL` запросы к API не выполняются.

## Локальный запуск

```bash
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
NEXT_PUBLIC_PROXY_URL=http://localhost:4040 \
npm run dev
```

Фронтенд требует доступного бэкенда по `NEXT_PUBLIC_API_BASE_URL` и прокси по `NEXT_PUBLIC_PROXY_URL`.

## Устранение неполадок

### Предупреждения SWC и lockfile при `npm run dev`

Если при запуске `npm run dev` вы видите предупреждения:
```
⚠ Found lockfile missing swc dependencies, patching...
⨯ Failed to patch lockfile, please try uninstalling and reinstalling next in this workspace
[TypeError: Cannot read properties of undefined (reading 'os')]
```

**Причина**: В репозитории существует `bun.lock`, но npm использует `package-lock.json`. Next.js пытается пропатчить lockfile для SWC-зависимостей и не находит ожидаемую структуру.

**Решение**:
1. Удалите `node_modules` и `package-lock.json` (если он существует):
   ```bash
   rm -rf node_modules package-lock.json
   ```
2. Переустановите зависимости:
   ```bash
   npm install
   ```
3. Если используете Bun вместо npm, выполните:
   ```bash
   rm -rf node_modules
   bun install
   ```

Это предупреждение **не ломает функциональность**, но может замедлить старт dev-сервера. После переустановки оно исчезнет или станет безвредным.

### Ошибки SSR с localStorage

Проект теперь использует безопасные хелперы для работы с `localStorage` из `src/shared/storage.ts` (а обёртки — в `src/utils/storage.ts`). Если вы добавляете новый код, работающий с `localStorage`:

- **Не используйте** `localStorage.getItem()` напрямую в рендере компонента или инициализаторах `useState`.
- **Используйте** хелперы из `src/utils/storage.ts`:
- `safeLocalStorageGet<T>(key, fallback)` — для безопасного чтения
- `safeLocalStorageSet<T>(key, value)` — для безопасной записи
- `getLocalStorageJSON<T>(key, defaultValue)` — для чтения JSON
- `setLocalStorageJSON<T>(key, value)` — для записи JSON

Эти хелперы автоматически проверяют `typeof window !== "undefined"` и безопасно парсят JSON, предотвращая краши во время SSR.

## Продакшн/Render

Вариант A (рекомендуемый): Render Web Service (Node.js)
1. Build command: `npm install && npm run build`
2. Start command: `npm run start`
3. Переменные окружения: `NEXT_PUBLIC_API_BASE_URL=https://<публичный-backend>`, `NEXT_PUBLIC_PROXY_URL=https://<публичный-proxy>`
4. Порт сервиса: 3000 (Render HTTP порт по умолчанию)

Вариант B: Docker Web Service
1. Используйте корневой `Dockerfile` (Next.js standalone образ).
2. Передайте те же переменные `NEXT_PUBLIC_API_BASE_URL` и `NEXT_PUBLIC_PROXY_URL`.
3. Откройте порт 3000.

Убедитесь, что бэкенд доступен с фронтенда; иначе страницы каталога и просмотр не работают.

## Зависимость от бэкенда

- Все данные каталога, поиска и авторизации приходят из FastAPI.
- При недоступности API страницы `/anime` и `/search/anime` отображают пустые/ошибочные состояния.
- Если бэкенд недоступен, UI может показывать пустые блоки без явных ошибок для пользователя (ошибки остаются только в консоли).

## Гибридные источники данных

- Часть маршрутов воспроизведения и поиска использует скрейперы HiAnime через API-роуты Next.js.
- FastAPI остаётся источником истины для основного каталога; скрейперы вспомогательные и могут отличаться по структуре данных.

## Ограничения текущего MVP

- UI авторизации неполный: не все потоки login/refresh выведены в интерфейс.
- Для некоторых аниме используются заглушки постеров/эпизодов, если бэкенд не возвращает данные.
- Работа с ошибками минимальна: при падении бэкенда блоки страниц отображают пустые результаты без подробных сообщений.
- Отсутствует изоляция от недоступности `NEXT_PUBLIC_PROXY_URL`: без прокси воспроизведение не работает.
