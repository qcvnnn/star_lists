"""Seed the local demo database or compare real PostgreSQL query plans."""
import argparse
import asyncio

from sqlalchemy import text

from db.session import engine

INDEX = "stars_catalog_received_date_idx"
DEMO_PREFIX = "Демо ДЗ #"
BENCHMARK = """
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, received_date
FROM stars
WHERE status = 'Опубликован' AND received_date = DATE '2025-01-14'
ORDER BY id LIMIT 10 OFFSET 20
"""


async def seed():
    async with engine.begin() as connection:
        await connection.execute(text("SELECT pg_advisory_xact_lock(712024)"))
        owner = await connection.scalar(text("SELECT min(id) FROM users"))
        if owner is None:
            raise SystemExit("Сначала зарегистрируйте пользователя через Swagger.")
        await connection.execute(text("""
            INSERT INTO stars (title, status, received_date, creator_id,
                               description, habitable_planets, formed_at)
            SELECT :prefix || n, 'Опубликован', DATE '2025-01-01' + (n % 730),
                   :owner, 'Учебная карточка звёздной системы.', n % 7, now()
            FROM generate_series(1, 100100) AS n
            WHERE (:prefix || n) NOT IN (
                SELECT title FROM stars WHERE left(title, length(:prefix)) = :prefix
            )
        """), {"prefix": DEMO_PREFIX, "owner": owner})
        await connection.execute(text("ANALYZE stars"))
        count = await connection.scalar(text(
            "SELECT count(*) FROM stars WHERE left(title, length(:prefix)) = :prefix"
        ), {"prefix": DEMO_PREFIX})
        print(f"Демо-карточек в базе: {count}")


async def benchmark():
    async with engine.connect() as connection:
        async with connection.begin():
            exists = await connection.scalar(text("SELECT to_regclass(:name)"), {"name": INDEX})
            if exists is None:
                raise SystemExit("Сначала выполните python -m alembic upgrade head.")
            await connection.execute(text("ANALYZE stars"))
        for indexed in (True, False):
            transaction = await connection.begin()
            try:
                if not indexed:
                    await connection.execute(text(f"DROP INDEX {INDEX}"))
                await connection.execute(text(BENCHMARK))  # warm buffers
                plan = await connection.scalars(text(BENCHMARK))
                print("\nС индексом" if indexed else "\nБез индекса")
                print("\n".join(plan))
            finally:
                await transaction.rollback()


async def main(action: str):
    try:
        await (seed() if action == "seed" else benchmark())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["seed", "benchmark"])
    asyncio.run(main(parser.parse_args().action))
