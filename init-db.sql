-- Initialisation de la base de données de production
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Configuration des performances
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';