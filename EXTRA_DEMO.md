# Показ допзадания

Из корня проекта в PowerShell:

```powershell
docker start postgres stars-redis minio_storage
python -m alembic upgrade head
python -m scripts.catalog_demo seed
python -m uvicorn main:app --reload
```

Генератор добавляет 100 100 учебных звёзд под существующим пользователем. При повторном запуске он пропускает уже созданные карточки. Если пользователей пока нет, зарегистрируйте одного через Swagger.

В другом терминале запустите `npm.cmd run dev` из `frontend` и откройте адрес, который покажет Vite. В плитке задайте дату **14.01.2025**, нажмите **«Найти»** и перейдите на следующую страницу. В Network покажите `GET /api/star_list/catalog?received_date=2025-01-14&page=2&limit=10`. В ответе видно, что сервер прислал 10 карточек и общее количество совпадений.

Из корня проекта запустите замер:

```powershell
python -m scripts.catalog_demo benchmark
```

Сравните тип плана, `Buffers` и `Execution Time` у одного запроса с индексом и без него. Скрипт удаляет индекс только внутри транзакции и восстанавливает его откатом.

Для показа Redis откройте приложение в новом окне инкогнито. На загрузке React запросит первую карточку. В DevTools → Application → Cookies скопируйте значение `feed_session`, затем подставьте его в команду:

```powershell
$feedKey = 'feed:guest:ПОДСТАВЬ_ЗНАЧЕНИЕ_COOKIE'
docker exec stars-redis redis-cli LLEN $feedKey
docker exec -it stars-redis redis-cli LRANGE $feedKey 0 99
```

Первая команда показывает 100 карточек, вторая — их ID с порядковыми номерами. После последней карточки следующий запрос заменяет подборку. Для демонстрации этого перехода можно взять последний ID из вывода и отправить `GET /api/star_list/feed?id=<ID>&next=true` с той же cookie.

[Схема взаимодействия](diagrams/catalog-feed-extra.md)
