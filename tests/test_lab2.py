"""Integration scenario in an isolated PostgreSQL schema, rolled back after the test."""
import asyncio
import importlib.util
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import httpx
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from api import handlers
from db.session import engine, get_db
from models import Star, User, Like
from data.media import DEFAULT_IMAGE, DEFAULT_VIDEO


def test_lab2_scenario():
    asyncio.run(run_scenario())


async def run_scenario():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        original_user = handlers.CURRENT_USER_ID
        schema = "test_lab2_" + uuid4().hex
        try:
            before = (await connection.execute(text(
                "SELECT (SELECT jsonb_agg(to_jsonb(s) ORDER BY id) FROM public.stars s)::text, "
                "(SELECT jsonb_agg(to_jsonb(u) ORDER BY id) FROM public.users u)::text, "
                "(SELECT jsonb_agg(to_jsonb(l) ORDER BY id) FROM public.likes l)::text"
            ))).one()
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))

            spec = importlib.util.spec_from_file_location("initial", Path(__file__).parents[1] / "alembic/versions/0001_initial_schema.py")
            migration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration)

            def migrate(sync_connection):
                with Operations.context(MigrationContext.configure(sync_connection)):
                    migration.upgrade()
            await connection.run_sync(migrate)

            async def override_db():
                async with AsyncSession(bind=connection, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as session:
                    yield session
            app.dependency_overrides[get_db] = override_db
            async with AsyncSession(bind=connection, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as session:
                user = User(username="test_user")
                other = User(username="other_user")
                session.add_all([user, other])
                await session.flush()
                handlers.CURRENT_USER_ID = original_test_user = user.id
                other_id = other.id
                await session.commit()

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/draft")
                assert r.status_code == 200 and DEFAULT_IMAGE in r.text and DEFAULT_VIDEO in r.text
                assert "disabled" not in r.text
                for title in ["", "  ", "x" * 101]:
                    assert (await client.post("/stars", data={"title": title})).status_code == 422
                r = await client.post("/stars", data={"title": "Test star"})
                assert r.status_code == 303 and r.headers["location"] == "/draft"

                async with AsyncSession(bind=connection, join_transaction_mode="create_savepoint") as session:
                    star = await session.scalar(select(Star))
                    star_id = star.id
                    assert star.status == "Черновик"
                    assert star.created_at and star.formed_at is None
                    assert star.image_url is None and star.video_url is None
                assert (await client.get(f"/feed?id={star_id}")).status_code == 404
                assert (await client.post("/stars", data={"title": "Duplicate"})).status_code == 303
                async with AsyncSession(bind=connection, join_transaction_mode="create_savepoint") as session:
                    assert await session.scalar(select(func.count(Star.id))) == 1
                payload = {"title": "Published star", "description": "Long description " * 20,
                           "received_date": "2026-09-15", "habitable_planets": "0"}
                assert (await client.post(f"/stars/{star_id}/publish", data={**payload, "habitable_planets": "-1"})).status_code == 422
                assert (await client.post(f"/stars/{star_id}/publish", data={**payload, "description": " "})).status_code == 422
                handlers.CURRENT_USER_ID = other_id
                assert (await client.post(f"/stars/{star_id}/publish", data=payload)).status_code == 404
                handlers.CURRENT_USER_ID = original_test_user
                r = await client.post(f"/stars/{star_id}/publish", data=payload)
                assert r.status_code == 303
                assert (await client.get(f"/feed?id={star_id}")).status_code == 200
                assert (await client.post(f"/stars/{star_id}/publish", data=payload)).status_code == 404
                async with AsyncSession(bind=connection, join_transaction_mode="create_savepoint") as session:
                    star = await session.get(Star, star_id)
                    assert star.formed_at is not None and star.habitable_planets == 0
                    session.add(Like(user_id=original_test_user, star_id=star_id))
                    star.image_url = "http://localhost:9000/media/missing-lab2.jpg"
                    star.video_url = "http://localhost:9000/media/missing-lab2.mp4"
                    await session.commit()

                with patch("data.media.httpx.AsyncClient.head", new=AsyncMock(side_effect=httpx.ConnectError("offline"))):
                    for url in [f"/feed?id={star_id}", "/catalog"]:
                        r = await client.get(url)
                        assert r.status_code == 200 and DEFAULT_IMAGE in r.text
                    assert DEFAULT_VIDEO in (await client.get(f"/feed?id={star_id}")).text
                r = await client.get("/catalog?received_date=2026-09-15")
                assert 'value="2026-09-15"' in r.text and "Published star" in r.text
                assert "<span>1</span>" in r.text
                assert "Published star" not in (await client.get("/catalog?received_date=2000-01-01")).text
                assert (await client.get("/catalog?received_date=bad")).status_code == 422
                assert (await client.get(f"/feed?id={star_id}&next=true")).status_code == 200
                handlers.CURRENT_USER_ID = other_id
                assert (await client.post(f"/stars/{star_id}/delete")).status_code == 404
                handlers.CURRENT_USER_ID = original_test_user
                assert (await client.post(f"/stars/{star_id}/delete")).status_code == 303
                assert (await client.get(f"/feed?id={star_id}")).status_code == 404
                assert "Published star" not in (await client.get("/catalog")).text
                assert (await client.post(f"/stars/{star_id}/delete")).status_code == 404
                async with AsyncSession(bind=connection, join_transaction_mode="create_savepoint") as session:
                    assert (await session.get(Star, star_id)).status == "Удален"
                    assert await session.scalar(select(func.count(Like.id))) == 1
                for url in [DEFAULT_IMAGE, DEFAULT_VIDEO]:
                    assert (await client.get(url)).status_code == 200
                assert len(handlers.router.routes) == 6
            after = (await connection.execute(text(
                "SELECT (SELECT jsonb_agg(to_jsonb(s) ORDER BY id) FROM public.stars s)::text, "
                "(SELECT jsonb_agg(to_jsonb(u) ORDER BY id) FROM public.users u)::text, "
                "(SELECT jsonb_agg(to_jsonb(l) ORDER BY id) FROM public.likes l)::text"
            ))).one()
            assert before == after
        finally:
            app.dependency_overrides.clear()
            handlers.CURRENT_USER_ID = original_user
            await transaction.rollback()
    await engine.dispose()
