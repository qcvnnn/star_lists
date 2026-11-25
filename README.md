# Дополнительные задания РИП

«Звёздные системы» — FastAPI, PostgreSQL, Redis и MinIO.

- **Индексы и пагинация.** Каталог принимает date через `received_date`, `page` и `limit`. Миграция добавляет частичный индекс по дате и ID. Redis хранит случайные подборки по 100 ID для ленты.
- **Tauri и CLIP.** [Нативный клиент](native/README.md) получает карточки по IPv4 локальной сети и сравнивает изображение с английскими описаниями через Transformers.js.

Настройте локальный .env по .env.example, запустите PostgreSQL, Redis и MinIO, установите зависимости из requirements.txt и примените `python -m alembic upgrade head`. Для React-клиента запустите FastAPI на порту 8000.

[React-клиент](frontend/README.md) · [Проверка индекса и Redis](EXTRA_DEMO.md) · [Диаграмма развёртывания](diagrams/stars-deployment.drawio)
