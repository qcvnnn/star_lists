# Дополнительное задание. Каталог и лента звёздных систем

```mermaid
sequenceDiagram
    actor Visitor as Гость или создатель
    participant React
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Cache as Redis

    Visitor->>React: Открыть приложение
    React->>API: GET /feed
    opt Есть cookie авторизации
        API->>Cache: GET session:session_id
        Cache-->>API: ID пользователя
    end
    API->>Cache: LRANGE списка для feed_session
    alt Списка ещё нет
        API->>DB: Случайные ID опубликованных звёзд, LIMIT 100
        DB-->>API: Уникальные ID
        API->>Cache: Сохранить упорядоченный список с TTL
    end
    API-->>React: Первая карточка и cookie feed_session
    Visitor->>React: Выбрать дату и страницу
    React->>API: GET /catalog?received_date=2025-01-14&page=3&limit=10
    API->>DB: COUNT и SELECT с индексом received_date, id
    DB-->>API: Число совпадений и карточки страницы
    API-->>React: data, total, page, limit
    loop Просмотр ленты
        Visitor->>React: Следующая карточка
        React->>API: GET /feed?id=123&next=true
        API->>Cache: Найти позицию текущей карточки
        opt Достигнут конец списка
            API->>DB: Случайная подборка, приоритет новым ID
            API->>Cache: Заменить список
        end
        API-->>React: Следующая карточка
    end
```

Для нового гостя ключ имеет вид `feed:guest:<feed_session>`. Для вошедшего пользователя ключ включает его ID. Индекс списка в Redis соответствует позиции карточки, начиная с нуля.
