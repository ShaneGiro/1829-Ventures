-- Runs once on first Postgres container start, BEFORE the first Alembic migration.
-- Enables the PostGIS (geography/map queries) and pgvector (semantic search)
-- extensions so migrations can create geometry and vector columns.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
