FROM postgres:17

# Install pgvector for PostgreSQL 17
RUN apt-get update && \
  apt-get install -y \
  postgresql-17-pgvector \
  && rm -rf /var/lib/apt/lists/*

# Initialize pgvector extension
COPY init-pgvector.sql /docker-entrypoint-initdb.d/
