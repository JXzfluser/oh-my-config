# oh-my-config

> 本地配置中心 + LLM Wiki + MCP Server - 项目一键接入 AI

## 解决什么问题？

- ❌ 每次和 AI 对话都要重新介绍项目配置
- ❌ 踩过的坑下次又忘了
- ❌ 配置找不到，四处翻记录
- ❌ AI 写代码不知道数据库连接信息
- ❌ AI 需要查数据时还要问你要账号密码

**oh-my-config** 就是来解决这些问题的。

## 核心功能

| 功能 | 用途 |
|------|------|
| **配置管理** | 存 MySQL, ES, Redis 等 |
| **Wiki 系统** | 项目知识库，AI 自动读取 |
| **规范文档** | CLAUDE.md, AGENTS.md 等 |
| **一键同步** | 同步到项目目录 |
| **AI 记录** | #log 指令自动记录知识 |
| **MCP Server** | AI 直接调用数据库工具 |

## 快速开始

### 1. 启动服务

```bash
cd /Users/zfl/projects/oh-my-config
uv run --with flask python3 server.py
```

服务运行在 `http://127.0.0.1:8848`

### 2. 初始化项目

```bash
# 初始化项目（自动扫描配置）
omc init /path/to/project

# 查看生成的项目配置
omc config /path/to/project
```

### 3. 启动 MCP Server

```bash
# 启动 MCP Server
omc mcp /path/to/project
```

### Web 管理界面

浏览器打开 http://127.0.0.1:8848

## CLI 命令

```bash
omc projects          # 列出所有项目
omc init [name] [path]   # 初始化项目
omc config [project]  # 查看项目配置
omc list <project>    # 列出项目配置
omc get <project> <type> <name>  # 获取配置
omc set <project> <type> <name> <content>  # 设置配置
omc mcp [project]    # 启动 MCP Server
omc sync <project>   # 同步到目录
```

## MCP Server 工具

启动 MCP Server 后，AI 可以直接调用以下工具：

### MySQL 操作

```python
# 执行 SQL 查询
mysql_query("SELECT * FROM users LIMIT 10")

# 返回结果示例
{"columns": ["id", "name", "email"], "rows": [[1, "张三", "zhangsan@example.com"]]}
```

### Redis 操作

```python
# 读取
redis_get("user:1")

# 写入
redis_set("user:1", '{"name": "张三", "age": 30}')
```

### Elasticsearch 操作

```python
# 搜索
es_search("users", '{"query": {"match": {"name": "张三"}}}')

# 计数
es_count("users")

# 写入文档
es_index("users", '{"name": "张三", "age": 30}')
```

### 项目信息

```python
# 获取项目信息
get_project_info()
# 返回: {"name": "myapp", "connections": ["mysql", "redis", "es"], "env": {...}}

# 加载项目配置
load_project("/path/to/project")
```

## 使用流程详解

### 方式 1: MCP Server（推荐）

```bash
# 1. 初始化项目（只需一次）
omc init /path/to/project

# 2. 启动 MCP Server
omc mcp /path/to/project

# 3. AI 直接调用工具
mysql_query("SELECT COUNT(*) FROM orders")
```

**优点**: AI 可以直接操作数据库，无需手动提供凭证

### 方式 2: 记住配置

```bash
# AI 记住项目配置
omc config /path/to/project

# AI 知道连接信息，写代码时自动带上正确的连接串
```

**优点**: 不需要启动额外进程，AI 记住配置后写代码自动带连接

## .omc.json 格式

项目初始化后，会在项目根目录生成 `.omc.json`：

```json
{
  "name": "myapp",
  "path": "/path/to/project",
  "profiles": ["dev"],
  "connections": {
    "mysql": "jdbc:mysql://localhost:3306/dbname",
    "redis": "redis://localhost:6379",
  "nacos": "http://localhost:8848",
  "rabbit": "rabbit://localhost:5672",
  "es": "http://localhost:9200"
  },
  "credentials": {
    "mysql_user": "root",
    "mysql_password": "your_password_here",
    "redis_password": "your_password_here",
    "es_user": "elastic",
    "es_password": "your_password_here"
  },
  "env": {
    "SPRING_PROFILES_ACTIVE": "dev",
    "SERVER_PORT": "8082"
  },
  "modules": ["web", "event", "bpm", "gateway"]
}
```

### 连接字符串格式

| 服务 | 格式 | 示例 |
|------|------|------|
| MySQL | `jdbc:mysql://host:port/dbname` | `jdbc:mysql://localhost:3306/myapp` |
| Redis | `redis://host:port` | `redis://localhost:6379` |
| ES | `http(s)://host:port` | `http://localhost:9200` |
| NACOS | `http(s)://host:port` | `https://nacos.example.com` |

## AI 调用示例

### SQL 查询

AI 收到用户请求：

```
sql> 查看今天有多少新用户
```

AI 自动调用：

```
mysql_query("SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURDATE()")
```

返回：`[{"COUNT(*)": 42}]`

### ES 搜索

AI 收到用户请求：

```
es> 搜索姓张的用户
```

AI 自动调用：

```
es_search("users", '{"query": {"match": {"name": "张"}}}')
```

### Redis 缓存

AI 收到用户请求：

```
redis> 查询用户 1 的 Session
```

AI 自动调用：

```
redis_get("session:user:1")
```

## 文件结构

```
oh-my-config/
├── server.py              # Flask API 服务
├── oh-my-config           # CLI 工具
├── mcp-server/
│   ├── server.py         # MCP Server
│   └── requirements.txt  # Python 依赖
├── static/
│   └── index.html       # Web UI
├── skills/
│   └── omc/
│       └── SKILL.md     # AI Skill
├── config.db             # SQLite 数据库
└── README.md           # 本文档
```

## 依赖安装

MCP Server 需要以下依赖：

```bash
# 方式 1: uv run（推荐）
uv run --with mcp --with mysql-connector-python --with redis --with elasticsearch python3 mcp-server/server.py

# 方式 2: 手动安装
pip install mcp mysql-connector-python redis elasticsearch
```

## AI 知识自动记录

### 触发指令

在 AI 对话中使用：

| 指令 | 用途 | 示例 |
|------|------|------|
| `#log xxx` | 记录发现/坑 | `#log ES 8.0 需要密码` |
| `#note xxx` | 记录笔记 | `#note 新工具: fzf` |
| `#rule xxx` | 记录规范 | `#rule 使用 try-catch` |

### API 调用

```bash
POST /api/log
Body: {"project": "项目名", "type": "log|note|rule", "content": "内容"}
```

## 更新日志

### 2026-04-26 (本次)

- 新增 MCP Server
- 支持 MySQL/Redis/ES 操作
- `omc init` 自动生成 `.omc.json`
- `omc config` 查看项目配置
- `omc mcp` 启动 MCP Server

### 2026-04-26

- 点击顶部-brand加载README
- 侧边栏收缩/展开功能
- AI 知识自动记录

### 2026-04-25

- 新增全局 Wiki 功能
- 项目删除功能