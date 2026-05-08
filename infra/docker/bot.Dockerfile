FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY bot ./bot
COPY shared ./shared

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "bot.main"]
