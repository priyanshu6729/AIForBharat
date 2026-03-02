CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS tenants (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  plan TEXT DEFAULT 'prototype',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  email TEXT NOT NULL,
  role TEXT DEFAULT 'member',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  name TEXT NOT NULL,
  default_language TEXT DEFAULT 'python',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS artifacts (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  type TEXT NOT NULL,
  s3_uri TEXT NOT NULL,
  checksum TEXT NOT NULL,
  size INT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_jobs (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  artifact_id INT REFERENCES artifacts(id),
  status TEXT DEFAULT 'queued',
  stage TEXT DEFAULT 'ingestion',
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ir_artifacts (
  id SERIAL PRIMARY KEY,
  artifact_id INT REFERENCES artifacts(id),
  s3_uri TEXT NOT NULL,
  language TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS code_entities (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  start_line INT NOT NULL,
  end_line INT NOT NULL,
  props_json JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS graph_nodes (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  type TEXT NOT NULL,
  entity_id INT REFERENCES code_entities(id),
  props_json JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS graph_edges (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  type TEXT NOT NULL,
  src_id INT REFERENCES graph_nodes(id),
  dst_id INT REFERENCES graph_nodes(id),
  props_json JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS graph_versions (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  s3_uri TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
  id SERIAL PRIMARY KEY,
  artifact_id INT REFERENCES artifacts(id),
  file_path TEXT NOT NULL,
  start_line INT NOT NULL,
  end_line INT NOT NULL,
  content_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  chunk_id INT REFERENCES chunks(id),
  vector vector(1536),
  model TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS queries (
  id SERIAL PRIMARY KEY,
  project_id INT REFERENCES projects(id),
  user_id INT REFERENCES users(id),
  question TEXT NOT NULL,
  mode TEXT DEFAULT 'explanation',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS answers (
  id SERIAL PRIMARY KEY,
  query_id INT REFERENCES queries(id),
  response TEXT NOT NULL,
  evidence_ids JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS learner_profiles (
  user_id INT PRIMARY KEY REFERENCES users(id),
  level TEXT DEFAULT 'beginner',
  preferences JSONB DEFAULT '{}'::jsonb,
  updated_at TIMESTAMP DEFAULT NOW()
);
