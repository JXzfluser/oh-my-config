import os
import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("oh-my-config")

PROJECT_CONFIG: dict = {}


def load_project_config(search_dir: str = ".") -> dict:
    search_path = Path(search_dir).resolve()
    
    for parent in [search_path] + list(search_path.parents):
        config_file = parent / ".omc.json"
        if config_file.exists():
            with open(config_file) as f:
                return json.load(f)
    
    return {}


def get_mysql_connection(config: dict):
    conn = config.get("connections", {}).get("mysql", "")
    if not conn:
        return None
    
    import re
    match = re.match(r"jdbc:mysql://([^:]+):(\d+)/(\w+)", conn)
    if match:
        host, port, db = match.groups()
        try:
            import mysql.connector
            return mysql.connector.connect(
                host=host,
                port=int(port),
                database=db,
                user=config.get("credentials", {}).get("mysql_user", "root"),
                password=config.get("credentials", {}).get("mysql_password", "")
            )
        except ImportError:
            try:
                import pymysql
                return pymysql.connect(
                    host=host,
                    port=int(port),
                    database=db,
                    user=config.get("credentials", {}).get("mysql_user", "root"),
                    password=config.get("credentials", {}).get("mysql_password", "")
                )
            except:
                return None
    return None


def get_redis_connection(config: dict):
    conn = config.get("connections", {}).get("redis", "")
    if not conn:
        return None
    
    import re
    match = re.match(r"redis://([^:]+):(\d+)", conn)
    if match:
        host, port = match.groups()
        try:
            import redis
            return redis.Redis(
                host=host,
                port=int(port),
                password=config.get("credentials", {}).get("redis_password", ""),
                decode_responses=True
            )
        except ImportError:
            return None
    return None


def get_es_connection(config: dict):
    conn = config.get("connections", {}).get("es", "")
    if not conn:
        return None
    
    try:
        from elasticsearch import Elasticsearch
        return Elasticsearch(
            [conn],
            basic_auth=(
                config.get("credentials", {}).get("es_user", "elastic"),
                config.get("credentials", {}).get("es_password", "")
            )
        )
    except ImportError:
        return None


@mcp.tool()
def mysql_query(query: str) -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config. Run 'omc init /path/to/project' first"})
    
    conn = get_mysql_connection(PROJECT_CONFIG)
    if not conn:
        return json.dumps({"error": "No MySQL configured in .omc.json"})
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            result = {"columns": columns, "rows": rows}
        else:
            conn.commit()
            result = {"affected_rows": cursor.rowcount}
        
        cursor.close()
        conn.close()
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redis_get(key: str) -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config"})
    
    r = get_redis_connection(PROJECT_CONFIG)
    if not r:
        return json.dumps({"error": "No Redis configured"})
    
    try:
        value = r.get(key)
        return json.dumps({"key": key, "value": value})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def redis_set(key: str, value: str) -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config"})
    
    r = get_redis_connection(PROJECT_CONFIG)
    if not r:
        return json.dumps({"error": "No Redis configured"})
    
    try:
        r.set(key, value)
        return json.dumps({"ok": True, "key": key})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def es_search(index: str, query: str) -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config"})
    
    es = get_es_connection(PROJECT_CONFIG)
    if not es:
        return json.dumps({"error": "No ES configured"})
    
    try:
        result = es.search(index=index, body=json.loads(query) if query.startswith("{") else {"query": {"match_all": {}}})
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def es_count(index: str, query: str = "{}") -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config"})
    
    es = get_es_connection(PROJECT_CONFIG)
    if not es:
        return json.dumps({"error": "No ES configured"})
    
    try:
        q = json.loads(query) if query.startswith("{") else {"query": {"match_all": {}}}
        result = es.count(index=index, body=q)
        return json.dumps({"count": result.get("count", 0)})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def es_index(index: str, document: str) -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config"})
    
    es = get_es_connection(PROJECT_CONFIG)
    if not es:
        return json.dumps({"error": "No ES configured"})
    
    try:
        doc = json.loads(document)
        es.index(index=index, document=doc)
        return json.dumps({"ok": True, "index": index})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_project_info() -> str:
    global PROJECT_CONFIG
    
    if not PROJECT_CONFIG:
        return json.dumps({"error": "No project config"})
    
    return json.dumps({
        "name": PROJECT_CONFIG.get("name"),
        "connections": list(PROJECT_CONFIG.get("connections", {}).keys()),
        "env": PROJECT_CONFIG.get("env", {})
    })


@mcp.tool()
def load_project(path: str) -> str:
    global PROJECT_CONFIG
    
    config = load_project_config(path)
    if config:
        PROJECT_CONFIG.update(config)
        return json.dumps({"ok": True, "project": config.get("name")})
    else:
        return json.dumps({"error": f"No .omc.json found in {path}"})


if __name__ == "__main__":
    import sys
    
    search_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    config = load_project_config(search_dir)
    if config:
        PROJECT_CONFIG.update(config)
        print(f"Loaded config for: {config.get('name')}")
    
    mcp.run()