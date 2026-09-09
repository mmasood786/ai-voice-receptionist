uv run alembic revision --autogenerate -m "add appointments"

uv run alembic upgrade head

uv run uvicorn app.main:app --reload


TRUNCATE TABLE
    messages,
    conversations,
    appointments,
    leads,
    customers
RESTART IDENTITY CASCADE;







