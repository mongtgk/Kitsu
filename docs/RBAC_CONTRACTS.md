# Соответствие эндпоинтов и разрешений

| Метод | Путь | Требуемое разрешение | Применение на сервере | Клиентские вызовы |
| --- | --- | --- | --- | --- |
| POST | /favorites | `write:content` | `Depends(require_enforced_permission)` | Кнопки избранного на `anime/[slug]` и `anime/watch` (disabled без права). |
| DELETE | /favorites/{anime_id} | `write:content` | `Depends(require_enforced_permission)` | Те же кнопки избранного; запрашивают DELETE с `anime_id` (slug/id). |
| POST | /watch/progress | `write:content` | `Depends(require_enforced_permission)` + валидация тела | UI пока не вызывает; подготовлено для синхронизации прогресса из плеера. |
| PATCH | /users/me | `write:profile` | `Depends(require_enforced_permission)` | Профиль может отправлять аватар (UI на данный момент не делает запрос). |

Остальные эндпоинты публичны или требуют только аутентификацию (Bearer), но не конкретного разрешения.
