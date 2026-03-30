# claude-bond

> 打包你和 Claude 的关系，让 Claude 在任何设备都认识你

claude-bond 捕获你与 Claude 之间独特的关系 -- 你的身份、行为规矩、沟通风格、技术偏好、工作上下文、工具链配置和共享记忆 -- 打包成可移植的 Markdown 文件，跟着你走。

## 为什么需要 claude-bond

- **换电脑**：公司电脑和家里电脑的 Claude 保持一致
- **分享**：把调教好的 Claude 关系分享给朋友
- **自动进化**：Claude 自动学习你的隐性习惯，越用越懂你
- **多身份**：工作/个人/项目级别的 bond 随时切换

## 安装

```bash
pip install claude-bond
```

要求：Python 3.11+，已安装 [Claude Code](https://claude.ai/code) CLI。

## 快速开始

### 1. 初始化你的 bond

```bash
bond init
```

扫描 `~/.claude/` 目录，Claude 自动分类你的配置到 7 个维度，交互式补充缺失信息。

不想回答问题？加 `--no-interview`：

```bash
bond init --no-interview
```

### 2. 应用到当前设备

```bash
bond apply
```

将 bond 写入 `~/.claude/CLAUDE.md`（Bond section）和 `~/.claude/memory/`，Claude Code 会自动读取。

### 3. 云同步（推荐）

最简单的跨设备同步，用 GitHub Gist：

```bash
# 初始化云同步（创建私有 Gist）
bond cloud init

# 日常同步
bond cloud

# 在新设备上拉取（用你的 Gist ID）
bond cloud pull --id <your-gist-id>
bond apply
```

### 4. 或者用文件分享

```bash
# 导出（可选加密）
bond export -o my.bond
bond export -o my.bond --encrypt

# 导入
bond import my.bond
bond import my.bond --password <密码>
```

### 5. 自动进化

安装 session hooks 后，Claude 会自动检测你的偏好变化：

```bash
# 安装 hooks
bond hooks --install

# 查看检测到的变化
bond review

# 或者开启自动合入
bond auto
```

## Bond 维度

claude-bond 将你和 Claude 的关系分为 7 个维度：

| 维度 | 文件 | 内容 |
|------|------|------|
| 用户画像 | `identity.md` | 角色、技术水平、知识背景 |
| 行为规矩 | `rules.md` | 你纠正/确认过的所有偏好 |
| 沟通风格 | `style.md` | 语言、语气、回复长度 |
| 记忆 | `memory.md` | 跨对话积累的事实性记忆 |
| 技术偏好 | `tech_prefs.md` | 框架、代码风格、架构偏好 |
| 工作上下文 | `work_context.md` | 项目、团队、deadline |
| 工具链 | `toolchain.md` | MCP servers、hooks、IDE 配置 |

所有文件都是人类可读的 Markdown，可以直接编辑：

```bash
bond edit          # 交互式编辑
bond edit rules    # 直接编辑指定维度
```

## Bond 文件结构

```
~/.claude-bond/
  ├── identity.md       # 用户画像
  ├── rules.md          # 行为规矩
  ├── style.md          # 沟通风格
  ├── memory.md         # 关键记忆
  ├── tech_prefs.md     # 技术偏好
  ├── work_context.md   # 工作上下文
  ├── toolchain.md      # 工具链配置
  ├── bond.yaml         # 元信息
  ├── pending/          # 待确认的变化
  ├── cloud.json        # 云同步配置
  └── tacit_signals.json # 默契模式数据
```

## 全部命令

### 核心命令

| 命令 | 说明 |
|------|------|
| `bond init [--no-interview]` | 初始化 bond，扫描 + AI 分类 + 对话补充 |
| `bond apply` | 应用 bond 到当前设备的 `~/.claude/` |
| `bond status` | 查看 bond 状态、维度概览、pending 数量 |
| `bond edit [dimension]` | 交互式编辑 bond 维度 |

### 同步与分享

| 命令 | 说明 |
|------|------|
| `bond cloud init` | 创建私有 GitHub Gist 作为云端 |
| `bond cloud` | 一键同步（pull + push） |
| `bond cloud push` | 推送到云端 |
| `bond cloud pull [--id ID]` | 从云端拉取 |
| `bond cloud status` | 查看云同步状态 |
| `bond sync [--init URL]` | Git 仓库同步（高级用户） |
| `bond export [-o file] [--encrypt]` | 导出为 .bond 文件（支持加密） |
| `bond import <file> [--password PW]` | 导入 .bond 文件 |

### 进化与审核

| 命令 | 说明 |
|------|------|
| `bond review` | 审核 pending 变化，逐条确认/丢弃 |
| `bond auto` | 自动合入高置信度变化 |
| `bond diff` | 查看上次 apply 以来 `~/.claude/` 的变化 |
| `bond tacit` | 查看默契模式检测到的隐性习惯 |
| `bond hooks --install` | 安装 Claude Code session hooks |
| `bond hooks --uninstall` | 卸载 hooks |

### 管理

| 命令 | 说明 |
|------|------|
| `bond doctor` | 健康检查（8 项诊断） |
| `bond profile list` | 列出所有 profile |
| `bond profile create <name> [--clone from]` | 创建新 profile |
| `bond profile use <name>` | 切换 profile |
| `bond profile delete <name>` | 删除 profile |
| `bond profile migrate` | 从旧版迁移到 profile 布局 |

## 进化机制

### 自动检测

每次 Claude Code session 结束，hook 自动：

1. 检测 `~/.claude/` 目录的文件变化（对比 snapshot）
2. 用 Claude 分析哪些变化涉及 bond 维度更新
3. 将变化写入 `pending/` 目录
4. 如果开启了自动模式，高置信度变化直接合入

### 默契模式

默契模式追踪你的隐性沟通习惯：

- 响应长度偏好（短/中/长）
- 语言使用模式
- 高频工作话题
- 重复纠正行为

需要至少 3 个 session 的数据才能开始检测。

```bash
bond tacit    # 查看检测到的模式
```

### 语义合并

当两台设备同时修改了同一维度，`bond sync` 会用 Claude 做语义合并 -- 智能去重，保留双方的独特内容，而非简单的 git 文本合并。

## 多 Profile 支持

为不同场景维护不同的 bond：

```bash
# 创建工作 profile（克隆自默认）
bond profile create work --clone default

# 切换到工作 profile
bond profile use work

# 修改工作 profile 的规矩
bond edit rules

# 切回默认
bond profile use default
```

## 加密导出

分享 bond 时保护隐私：

```bash
# 加密导出（会要求输入密码）
bond export -o my.bond --encrypt

# 对方导入时需要密码
bond import my.bond --password <密码>
```

使用 AES-256 加密，PBKDF2 密钥派生（600,000 次迭代）。

## 后端优先级

claude-bond 按以下顺序选择 AI 后端：

1. **Claude Code CLI** (`claude -p`) -- 使用你的 Claude 订阅，无需 API key
2. **Anthropic API** -- 需要设置 `ANTHROPIC_API_KEY`
3. **离线模式** -- 关键词匹配分类（精度有限）

大多数用户只需安装 Claude Code 即可，不需要 API key。

## 技术栈

- **CLI 框架**: Typer
- **AI 后端**: Claude Code CLI / Anthropic SDK
- **加密**: PBKDF2 + HMAC-SHA256
- **云同步**: GitHub Gist (via `gh` CLI)
- **Git 同步**: subprocess
- **输出格式化**: Rich

## 给 Claude 的说明

如果你是 Claude，正在阅读这个项目的代码：

- Bond 文件使用 YAML frontmatter + Markdown 内容格式
- 每个维度文件的 frontmatter 包含 `dimension`、`updated`、`source` 字段
- `bond apply` 在 CLAUDE.md 中用 `<!-- bond:start -->` / `<!-- bond:end -->` 标记管理 bond section
- 不要修改标记之外的内容
- `pending/` 目录下的文件格式遵循 `## New` / `## Updated` / `## Possible (low confidence)` 分区
- 每条 pending 项格式为 `- [dimension] description`

## License

MIT
