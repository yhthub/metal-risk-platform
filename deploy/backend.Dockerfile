FROM python:3.11-slim-bookworm
ARG INSTALL_MEDCPT=false
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
COPY backend/requirements-retrieval-optional.txt /app/requirements-retrieval-optional.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && if [ "$INSTALL_MEDCPT" = "true" ]; then \
         pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu 'torch>=2.4,<3' \
         && pip install --no-cache-dir -r /app/requirements-retrieval-optional.txt; \
       elif [ "$INSTALL_MEDCPT" != "false" ]; then \
         echo 'INSTALL_MEDCPT must be true or false' >&2; exit 1; \
       fi \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home app \
    && mkdir -p /data/uploads \
    && chown app:app /data/uploads
# Optional embedding dependencies are CPU-only and explicit; no weights are downloaded.
# Pin the resulting lock/image for the target platform before production use.
# Do not copy backend/.env, uploaded records, model weights, or the entire repository.
COPY --chown=app:app backend/app /app/app
USER 10001:10001
EXPOSE 8000
# One worker keeps in-process concurrency/rate limits consistent. Scale only after a shared limiter exists.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
