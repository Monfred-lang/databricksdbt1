#!/usr/bin/env python3
"""Run dbt deps, seed, snapshot, run, test. Requires DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN."""
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(REPO_ROOT, ".dbt")
PROFILES_FILE = os.path.join(PROFILES_DIR, "profiles.yml")


def main():
    os.chdir(REPO_ROOT)

    host = os.environ.get("DATABRICKS_HOST")
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")
    token = os.environ.get("DATABRICKS_TOKEN")
    schema = os.environ.get("DBT_SCHEMA", "silver")
    catalog = os.environ.get("DATABRICKS_CATALOG", "workspace")

    if not all([host, http_path, token]):
        print("Missing required env: DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN", file=sys.stderr)
        sys.exit(1)

    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(PROFILES_FILE, "w") as f:
        f.write(f"""shopflow_analytics:
  target: prod
  outputs:
    prod:
      type: databricks
      host: "{host}"
      http_path: "{http_path}"
      schema: "{schema}"
      catalog: "{catalog}"
      token: "{token}"
      threads: 4
      connect_timeout: 60
      connect_retries: 3
""")

    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = PROFILES_DIR

    for cmd in [["dbt", "deps"], ["dbt", "seed"], ["dbt", "run"], ["dbt", "snapshot"], ["dbt", "test"]]:
        print(f"Running: {' '.join(cmd)}")
        r = subprocess.run(cmd, env=env, cwd=REPO_ROOT)
        if r.returncode != 0:
            sys.exit(r.returncode)
    print("dbt pipeline completed successfully.")


if __name__ == "__main__":
    main()
