from typing import Dict, Any

# In-memory storage to gracefully handle scenarios where external Postgres or Redis is temporarily unreachable
in_memory_jobs: Dict[str, Any] = {}
in_memory_submissions: Dict[str, Any] = {}
in_memory_results: Dict[str, Any] = {}
