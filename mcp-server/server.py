import os
import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("oh-my-config")

PROJECT_CONFIG: dict = {}
CURRENT_PROJECT: str = ""

API = os.environ.get("OMC_API", "http://127.0.0.1:8848")


def load_from_api(project: str) -> dict:
    import urllib.request
    
    try:
        url = f"{API}/api/configs/{project}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            configs = json.loads(resp.read().decode())
        
        result = {"name": project, "connections": {}, "credentials": {}, "env": {}}
        for c in configs:
            if c["type"] == "config":
                name = c["name"]
                try:
                    data = json.loads(c["content"]) if c["content"].startswith("{") else {}
                except:
                    data = {"raw": c["content"]}
                
                if name == "MYSQL":
                    url = data.get("url", "")
                    if url.startswith("jdbc:"):
                        result["connections"]["mysql"] = url
                    result["credentials"]["mysql_user"] = data.get("username", "")
                    result["credentials"]["mysql_password"] = data.get("password", "")
                elif name == "REDIS":
                    if "host" in data:
                        result["connections"]["redis"] = f"redis://{data['host']}:{data.get('port', 6379)}"
                        result["credentials"]["redis_password"] = data.get("password", "")
                elif name == "NACOS":
                    if "serverAddr" in data:
                        result["connections"]["nacos"] = f"http://{data['serverAddr']}"
                        result["credentials"]["nacos_user"] = data.get("username", "")
                        result["credentials"]["nacos_password"] = data.get("password", "")
        
        return result
    except Exception as e:
        print(f"Error loading from API: {e}")
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
    global PROJECT_CONFIG, CURRENT_PROJECT
    
    if not CURRENT_PROJECT:
        return json.dumps({"error": "No project selected. Run 'omc mcp project' first"})
    
    return json.dumps({
        "name": CURRENT_PROJECT,
        "connections": list(PROJECT_CONFIG.get("connections", {}).keys()),
    })


@mcp.tool()
def load_project(project: str) -> str:
    global PROJECT_CONFIG, CURRENT_PROJECT
    
    config = load_from_api(project)
    if config and config.get("connections"):
        PROJECT_CONFIG.update(config)
        CURRENT_PROJECT = project
        return json.dumps({"ok": True, "project": project, "connections": list(config.get("connections", {}).keys())})
    else:
        return json.dumps({"error": f"No config found for project: {project}"})


if __name__ == "__main__":
    import sys
    
    project = sys.argv[1] if len(sys.argv) > 1 else None
    if project:
        config = load_from_api(project)
        if config:
            PROJECT_CONFIG.update(config)
            CURRENT_PROJECT = project
            print(f"Loaded config for: {project}")
        else:
            print(f"Warning: No config found for: {project}")
    
    mcp.run()