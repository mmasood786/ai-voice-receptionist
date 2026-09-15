uv run alembic revision --autogenerate -m "add appointments"

uv run alembic upgrade head

uv run uvicorn app.main:app --reload

all-MiniLM-L6-v2   (384)


TRUNCATE TABLE
    messages,
    conversations,
    appointments,
    leads,
    customers
RESTART IDENTITY CASCADE;


git init
git add .
git commit -m "Initial commit"

git branch -M main
git remote add origin https://github.com/USERNAME/my-project.git

git push -u origin main

git add .
git commit -m "Describe your changes"
git push








