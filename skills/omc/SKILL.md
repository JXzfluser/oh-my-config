# omc

> 本地配置中心 + LLM Wiki - 符合 Karpathy 理念

## 启动服务

```bash
cd ~/projects/oh-my-config
uv run --with flask python3 server.py
```

服务: http://127.0.0.1:8848

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

## CLI 命令

```bash
omc projects          # 列出项目
omc init myapp       # 初始化项目
omc list -p myapp   # 列出配置
omc get myapp MYSQL  # 获取配置
omc sync myapp      # 同步到目录
```

## 在 OpenCode 中使用

AI 会先读取全局 Wiki (`__GLOBAL__`) 获取共享知识，再到项目 Wiki 获取项目特定内容。

### 使用流程

1. 读取 `wiki/INDEX.md` 了解 Wiki 结构
2. 根据 INDEX 找到相关页面
3. 深入阅读实体/概念页
4. 有价值的发现写入 LOG.md

### 知识沉淀

- 好的答案写回 Wiki (知识复合)
- 不要每次重新推导，要复用已有 Wiki
- 实体页: 人/组织/工具等具体事物
- 概念页: 模式/方法论等抽象知识