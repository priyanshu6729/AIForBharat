# Prototype Architecture

Three services:

- Ingestion: accepts artifacts and queues jobs
- Analysis: parses, builds graphs, embeds
- Query: retrieves context and runs LLM reasoning

Storage:
- S3 for raw code and snapshots
- Postgres + pgvector for metadata, graphs, embeddings
