# oh-my-config

> 本地配置中心 + LLM Wiki - 符合 Karpathy 理念的知识管理

## 核心概念

### LLM Wiki 架构 (Karpathy 理念)

```
全局 Wiki (__GLOBAL__)
├── INDEX.md     - 全局目录 (所有项目共享知识)
├── LOG.md      - 变更记录 (AI 探索发现)
├── ENTITIES.md - 实体索引 (人/组织/工具)
└── CONCEPTS.md - 概念索引 (模式/方法论)

项目 Wiki (每个项目独立)
├── INDEX.md   - 项目目录
├── LOG.md     - 项目变更
└── *.md       - 项目文档
```

### 设计原则

1. **全局 Wiki** - 存放所有项目共享的知识
2. **项目 Wiki** - 存放单个项目特有的内容
3. **INDEX.md** - 每个 Wiki 的全局目录
4. **LOG.md** - 记录 AI 的探索和发现

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
./oh-my-config projects          # 列出项目
./oh-my-config init myapp       # 初始化项目
./oh-my-config get myapp MYSQL   # 获取配置
./oh-my-config set myapp key value
./oh-my-config sync myapp       # 同步到目录
```

## 主要功能

1. **配置管理** - 项目配置存储和读取
2. **Wiki 系统** - 全局 Wiki + 项目 Wiki
3. **规范文档** - CLAUDE.md, AGENTS.md, GEMINI.md
4. **一键同步** - 同步到项目目录

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

### 2026-04-25

- 新增全局 Wiki 功能
- 项目删除功能
- 分离全局 Wiki 和项目 Wiki UI