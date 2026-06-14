# Postgres 16 with BOTH PostGIS and pgvector.
# The official postgis image ships PostGIS but not pgvector; we add pgvector from
# the PGDG apt repo (already configured in the base image).
FROM postgis/postgis:16-3.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
