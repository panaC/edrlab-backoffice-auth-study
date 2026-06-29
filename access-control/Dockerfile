FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY src /app/src
COPY tests /app/tests

RUN useradd --system --create-home --home-dir /app app \
    && mkdir -p /app/runtime/state /app/runtime/audit /app/evidence \
    && chown -R app:app /app

USER app

EXPOSE 8000 8001

CMD ["python", "-m", "access_control.iam_api"]

