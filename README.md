# oh-my-config

> 本地配置中心 + LLM Wiki - 符合 Karpathy 理念的知识管理

## 解决什么问题？

当你在多个项目之间切换时，是否遇到过：

- ❌ 每次和 AI 对话都要重新介绍项目配置
- ❌ 踩过的坑下次又忘了
- ❌ 配置找不到，四处翻记录
- ❌ 项目规范不统一

**oh-my-config** 就是来解决这些问题的。

## 核心功能

| 功能 | 用途 |
|------|------|
| **配置管理** | 存 MySQL, ES, API keys 等 |
| **Wiki 系统** | 项目知识库，AI 自动读取 |
| **规范文档** | CLAUDE.md, AGENTS.md 等 |
| **一键同步** | 同步到项目目录 |
| **AI 记录** | #log 指令自动记录知识 |

## 快速开始

### 启动服务

```bash
cd /Users/zfl/projects/oh-my-config
uv run --with flask python3 server.py
```

服务运行在 `http://127.0.0.1:8848`

### Web 管理界面

浏览器打开 http://127.0.0.1:8848

### CLI 使用

```bash
omc projects          # 列出项目
omc init myapp       # 初始化项目
omc get myapp MYSQL  # 获取配置
omc set myapp key value
omc sync myapp       # 同步到目录
omc open            # 打开 Web 界面
```

## 什么时候用？

### 场景 1: 新项目启动

```
1. 打开 oh-my-config Web 界面
2. 创建新项目 (如: myapp)
3. 添加配置 (MySQL, ES, Redis 等)
4. 添加 Wiki (项目说明、技术栈)
5. 添加规范 (代码规范、提交规范)
6. 点击"同步"下发到项目目录
```

### 场景 2: 和 AI 对话

```
1. 告诉 AI 项目名
2. AI 自动读取项目配置和 Wiki
3. 使用 #log 记录新发现
4. AI 下次会自动记住
```

### 场景 3: 切换项目

```
1. 切换项目
2. 配置自动切换
3. AI 自动读取新项目知识
```

### 场景 4: 记录发现

```
和 AI 对话时:
- #log ES 8.0 需要密码认证
- #note 新工具: fzf
- #rule 提交前先跑测试
```

AI 会自动记录到当前项目的 LOG.md。

## 主要功能
- **配置管理** - 项目配置存储和读取
- **Wiki 系统** - 全局 Wiki + 项目 Wiki
- **规范文档** - CLAUDE.md, AGENTS.md, GEMINI.md
- **一键同步** - 同步到项目目录
- **AI 记录** - #log/#note/#rule 指令自动记录到项目 Wiki

## AI 知识自动记录

### 触发指令

在 AI 对话中使用：

| 指令 | 用途 | 示例 |
|------|------|------|
| `#log xxx` | 记录发现/坑 | `#log ES 8.0 需要密码` |
| `#note xxx` | 记录笔记 | `#note 新工具: fzf` |
| `#rule xxx` | 记录规范 | `#rule 使用 try-catch` |

### 记录规则

- 只记录到**当前项目**的 Wiki
- 记录到项目的 LOG.md
- AI 可通过 API 自动写入

### API 调用

AI 记录时自动调用：

```bash
POST /api/log
Body: {"project": "项目名", "type": "log|note|rule", "content": "内容"}
```

## 配置模板

- ENV, MYSQL, REDIS, MONGODB
- ELASTICSEARCH, KAFKA, RABBITMQ
- SMTP, ALIPAY, WECHAT

## 文件结构

```
oh-my-config/
├── server.py           # Flask 服务
├── oh-my-config      # CLI 工具
├── static/
│   └── index.html  # Web UI
├── skills/
│   └── oh-my-config/
│       └── SKILL.md
└── templates/       # 配置模板
```

## 更新日志

### 2026-04-26

- 点击顶部-brand加载README
- 侧边栏收缩/展开功能
- 收缩后显示迷你导航(展开/首页/全局/新建)
- AI 知识自动记录 (#log/#note/#rule)

### 2026-04-25

- 新增全局 Wiki 功能
- 项目删除功能
- 分离全局 Wiki 和项目 Wiki UI