# Codexa Prototype API

- Ingestion service: `/upload`, `/analyze`, `/status/{job_id}`
- Analysis service: `/jobs/{job_id}/run`, `/jobs/run-next`
- Query service: `/query`

Refer to service router files for request and response details.

Notes:
- `repo_url` ingestion requires `git` to be available and network access to the repository.
