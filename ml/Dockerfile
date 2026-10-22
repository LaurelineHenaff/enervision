FROM python:3.13-slim

# GIT_PYTHON_REFRESH : MLflow cherche git pour tracer le commit, absent de l'image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GIT_PYTHON_REFRESH=quiet

# Utilisateur non-root pour exécuter le module ML
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --no-create-home app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .

# Version du code, passée par la CI à la construction
ARG GIT_TITLE=dev
ARG GIT_SHA=dev
ENV GIT_TITLE=$GIT_TITLE \
    GIT_SHA=$GIT_SHA

USER app

CMD ["python", "train.py"]
