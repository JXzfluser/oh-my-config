# omc

> 本地配置中心 + LLM Wiki + MCP Server - 项目一键接入 AI

## 快速开始

```bash
# 1. 启动服务
cd ~/projects/oh-my-config
uv run --with flask python3 server.py

# 2. 初始化项目（只需一次）
omc init /path/to/project

# 3. 启动 MCP Server（AI 需要操作数据库时）
omc mcp /path/to/project
```

## 核心概念

### LLM Wiki 架构 (Karpathy 理念)

**全局 Wiki** (`__GLOBAL__`)：
- INDEX.md - 全局目录 (所有项目共享知识)
- LOG.md - 变更记录 (AI 探索发现)
- ENTITIES.md - 实体索引
- CONCEPTS.md - 概念索引

**项目 Wiki** (每个项目独立)：
- 项目自己的 .md 文件

### 配置类型

- **Wiki** - 项目知识库
- **Spec** - 规范 (CLAUDE.md, AGENTS.md, GEMINI.md)
- **Config** - 服务配置 (JSON)

## MCP Server（核心功能）

AI 可以直接操作数据库的工具：

### MySQL

```python
# 执行 SQL
mysql_query("SELECT * FROM users LIMIT 10")
mysql_query("INSERT INTO logs (msg) VALUES ('hello')")
mysql_query("UPDATE users SET name='新名字' WHERE id=1")
```

### Redis

```python
# 读写缓存
redis_get("user:1")
redis_set("user:1", '{"name": "张三"}')
```

### Elasticsearch

```python
# 搜索
es_search("users", '{"query": {"match": {"name": "张"}}}')
es_count("users")
es_index("users", '{"name": "李四", "age": 25}')
```

### 项目信息

```python
# 查看配置
get_project_info()
load_project("/path/to/project")
```

## CLI 命令

```bash
# 项目管理
omc projects              # 列出所有项目
omc init [name] [path]   # 初始化项目
omc config [project]     # 查看项目配置
omc list <project>      # 列出配置
omc get <project> <type> <name>  # 获取配置
omc set <project> <type> <name> <content>  # 设置配置
omc sync <project>     # 同步到目录

# MCP Server
omc mcp [project]    # 启动 MCP Server
```

## 使用流程

### 方式 1: MCP Server（推荐）

```bash
# 1. 初始化项目（只需一次）
omc init /path/to/project
# → 自动扫描 bootstrap*.yml
# → 生成 .omc.json

# 2. 启动 MCP Server
omc mcp /path/to/project

# 3. AI 直接调用工具
mysql_query("SELECT COUNT(*) FROM orders")
```

### 方式 2: 记住配置

```bash
# 查看配置
omc config /path/to/project

# AI 记住后写代码自动带连接串
```

## 项目初始化

### 自动扫描

```bash
omc init /path/to/project
```

**自动扫描内容：**
- bootstrap*.yml → MySQL, Redis, NACOS 等配置
- pom.xml → 技术栈
- README.md → 项目说明

**生成文件：**
- `.omc.json` - 项目配置（包含连接字符串和凭证）

### 连接字符串格式

| 服务 | 格式 | 示例 |
|------|------|------|
| MySQL | `jdbc:mysql://host:port/dbname` | `jdbc:mysql://localhost:3306/myapp` |
| Redis | `redis://host:port` | `redis://localhost:6379` |
| ES | `http://host:port` | `http://localhost:9200` |

## 知识自动记录

### 触发指令

| 指令 | 用途 | 示例 |
|------|------|------|
| `#log xxx` | 记录发现/坑 | `#log ES 8.0 需要密码` |
| `#note xxx` | 记录笔记 | `#note 新工具: fzf` |
| `#rule xxx` | 记录规范 | `#rule 使用 try-catch` |

### API 调用

```
POST /api/log
Body: {"project": "项目名", "type": "log|note|rule", "content": "内容"}
```

## 在 OpenCode 中使用

### AI 使用 MCP

1. 用户启动 MCP Server: `omc mcp .`
2. AI 收到工具列��
3. AI 根据需求调用对应工具

### AI 记住配置

1. 用户告诉 AI 项目名
2. AI 调用 `omc config .` 读取配置
3. AI 记住连接信息