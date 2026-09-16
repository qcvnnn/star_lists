# Звёздные системы — лабораторная №2

Ветка: feature/database-integration.

Лабораторная №2: подключение PostgreSQL, получение и фильтрация звёзд через ORM, создание черновиков, публикация и логическое удаление карточек. Лайки читаются из БД, отсутствующие медиа заменяются локальными файлами.

FastAPI, Jinja2, PostgreSQL, SQLAlchemy AsyncSession, asyncpg, Alembic,
Pydantic Settings. HTML и CSS без JavaScript.

## Запуск на текущем компьютере

~~~powershell
python -m pip install -r requirements.txt
docker start postgres
docker compose up -d
python -m alembic current
python -m uvicorn main:app --reload
~~~

Открыть http://127.0.0.1:8000/feed или /draft, /catalog.
Adminer: http://127.0.0.1:8080; сервер postgres, БД stars_db.
Пользователь и пароль подключения находятся в локальном .env.
PostgreSQL уже запущен отдельным контейнером, порт хоста 5455.
Compose управляет существующими MinIO и Adminer; не создаёт вторую БД.

## Настройки

.env не попадает в Git. На другом компьютере скопировать .env.example в .env
и указать своё подключение. CURRENT_USER_ID=1 — демонстрационный пользователь
без авторизации. Смена этого значения требует перезапуска приложения.

## Файлы

- core/config.py — Pydantic Settings, чтение .env.
- db/base.py, db/session.py — общая Base, async engine, сессии БД.
- models/user.py, models/star.py, models/like.py — модели существующих таблиц.
- api/handlers.py — шесть обработчиков.
- data/media.py — асинхронная проверка URL и локальные файлы по умолчанию.
- templates/ — три Jinja2-шаблона.
- static/media/ — фото и видео по умолчанию.
- alembic/versions/0001_initial_schema.py — начальная схема.
- data/collections.py — старые данные первой лабы, приложение их не импортирует.
- docs/lab2.md — порядок показа и пояснения.
- docs/stars.mdj — ER-диаграмма для StarUML.
- tests/test_lab2.py — сценарий в отдельной временной схеме PostgreSQL.

## Маршруты

| Метод | URL | Назначение |
|---|---|---|
| GET | /feed?id=1&next=true | Лента, следующая опубликованная звезда |
| GET | /draft | Черновик текущего пользователя или пустая форма |
| GET | /catalog?received_date=2025-05-21 | Каталог с фильтром по дате |
| POST | /stars | Создание черновика через ORM |
| POST | /stars/{star_id}/publish | Публикация через ORM |
| POST | /stars/{star_id}/delete | Логическое удаление параметризованным SQL UPDATE |

После POST выполняется перенаправление 303 на GET.
Создание и публикация не передают медиафайлы на сервер.
При публикации заполняется formed_at; created_at назначает PostgreSQL.
Для удалённой или неопубликованной карточки GET ленты возвращает 404.
Лайки считаются из таблицы likes, изменять их из приложения нельзя.

## Alembic и существующая база

Схема stars_db проверена на совпадение с моделями, после этого выполнено
alembic stamp 0001. Таблицы и данные не пересоздавались.
Alembic добавляет только свою служебную таблицу alembic_version.

Для новой ПУСТОЙ базы: python -m alembic upgrade head.
Для изменения схемы: изменить модели, выполнить
python -m alembic revision --autogenerate -m "description",
проверить созданную миграцию, затем python -m alembic upgrade head.
Не применять создание исходных таблиц повторно к уже заполненной БД.
Проверить соответствие: python -m alembic check.

## Проверка

~~~powershell
python -m pytest -q
~~~

Тест создаёт временную схему в транзакции, применяет исходную миграцию,
проверяет создание, публикацию, удаление, фильтр, лайки и медиа.
Все тестовые данные откатываются. Основные таблицы не меняются.
