# claude-bond

**[English](#english) | [中文](#中文)**

---

<a id="english"></a>

> Package your relationship with Claude. Make Claude recognize you on any device.

claude-bond captures the unique relationship between you and Claude -- your identity, behavioral rules, communication style, technical preferences, work context, toolchain config, and shared memories -- into portable Markdown files that travel with you.

## Why claude-bond

- **Switch devices**: Keep Claude consistent between work and home computers
- **Share**: Share your fine-tuned Claude relationship with friends
- **Auto-evolve**: Claude automatically learns your implicit habits over time
- **Multi-identity**: Switch between work/personal/project-specific bonds

## Install

```bash
pip install claude-bond
```

Requirements: Python 3.11+, [Claude Code](https://claude.ai/code) CLI installed.

## Quick Start

### Step 1: Initialize on your primary device (Device A)

```bash
# 1. Install
pip install claude-bond

# 2. Initialize -- scan your ~/.claude/ config, Claude auto-classifies
bond init

# 3. Apply to current device (writes to ~/.claude/CLAUDE.md and memory)
bond apply

# 4. Enable cloud sync (creates a private GitHub Gist)
bond cloud init
# → Output: Gist ID: abc123def456  ← remember this ID
```

Done. Your Claude relationship is now packaged.

### Step 2: Restore on a new device (Device B)

```bash
# 1. Install
pip install claude-bond

# 2. Pull your bond (using the Gist ID from Device A)
bond cloud pull --id abc123def456

# 3. Apply
bond apply

# Done! Claude on Device B now recognizes you
```

### Daily Usage

```bash
bond cloud          # One-click sync (run on any device)
bond status         # View bond status
bond edit           # Manually edit bond dimensions
bond diff           # View changes since last apply
```

### Share with Friends

```bash
# You: export (optionally encrypted)
bond export -o my.bond
bond export -o my.bond --encrypt

# Friend: import
bond import my.bond
bond import my.bond --password <password>
```

### Auto-Evolution (Optional)

Install session hooks and Claude will automatically detect preference changes after each session:

```bash
bond hooks --install    # Install hooks (one-time)
bond review             # Review detected changes
bond auto               # Or enable auto-merge
bond tacit              # View tacit mode patterns
```

## Bond Dimensions

claude-bond organizes your Claude relationship into 7 dimensions:

| Dimension | File | Content |
|-----------|------|---------|
| Identity | `identity.md` | Role, expertise, background |
| Rules | `rules.md` | Behavioral preferences you've set |
| Style | `style.md` | Language, tone, verbosity |
| Memory | `memory.md` | Cross-session factual memories |
| Tech Prefs | `tech_prefs.md` | Frameworks, code style, patterns |
| Work Context | `work_context.md` | Projects, team, deadlines |
| Toolchain | `toolchain.md` | MCP servers, hooks, IDE config |

All files are human-readable Markdown. Edit directly:

```bash
bond edit          # Interactive editor
bond edit rules    # Edit specific dimension
```

## File Structure

```
~/.claude-bond/
  ├── identity.md       # Identity
  ├── rules.md          # Rules
  ├── style.md          # Style
  ├── memory.md         # Memory
  ├── tech_prefs.md     # Technical preferences
  ├── work_context.md   # Work context
  ├── toolchain.md      # Toolchain
  ├── bond.yaml         # Metadata
  ├── pending/          # Changes awaiting review
  ├── cloud.json        # Cloud sync config
  └── tacit_signals.json # Tacit mode data
```

## All Commands

### Core

| Command | Description |
|---------|-------------|
| `bond init [--no-interview]` | Initialize bond (scan + AI classify + interview) |
| `bond apply` | Apply bond to `~/.claude/` |
| `bond status` | View bond status and dimension overview |
| `bond edit [dimension]` | Interactive dimension editor |

### Sync & Share

| Command | Description |
|---------|-------------|
| `bond cloud init` | Create private GitHub Gist |
| `bond cloud` | One-click sync (pull + push) |
| `bond cloud push` | Push to cloud |
| `bond cloud pull [--id ID]` | Pull from cloud |
| `bond cloud status` | View cloud sync status |
| `bond sync [--init URL]` | Git repo sync (advanced) |
| `bond export [-o file] [--encrypt]` | Export as .bond file |
| `bond import <file> [--password PW]` | Import .bond file |

### Evolution

| Command | Description |
|---------|-------------|
| `bond review` | Review pending changes |
| `bond auto` | Auto-merge high-confidence changes |
| `bond diff` | View changes since last apply |
| `bond tacit` | View tacit mode patterns |
| `bond hooks --install` | Install Claude Code session hooks |
| `bond hooks --uninstall` | Remove hooks |

### Management

| Command | Description |
|---------|-------------|
| `bond doctor` | Health check (8 diagnostics) |
| `bond profile list` | List all profiles |
| `bond profile create <name> [--clone from]` | Create new profile |
| `bond profile use <name>` | Switch profile |
| `bond profile delete <name>` | Delete profile |
| `bond profile migrate` | Migrate to profile layout |

## How Evolution Works

### Auto-Detection

After each Claude Code session, hooks automatically:

1. Detect file changes in `~/.claude/` (compared to snapshot)
2. Ask Claude to classify changes into bond dimensions
3. Write changes to `pending/` directory
4. If auto-mode is enabled, merge high-confidence changes

### Tacit Mode

Tracks implicit communication habits:

- Response length preference (short/medium/long)
- Language usage patterns
- Frequent work topics
- Repeated corrections

Requires at least 3 sessions of data.

### Semantic Merge

When two devices modify the same dimension, `bond sync` uses Claude for semantic merging -- intelligent deduplication that preserves unique content from both sides.

## Multi-Profile

Maintain different bonds for different contexts:

```bash
bond profile create work --clone default
bond profile use work
bond edit rules
bond profile use default
```

## Encrypted Export

Protect privacy when sharing:

```bash
bond export -o my.bond --encrypt
bond import my.bond --password <password>
```

Uses PBKDF2 key derivation (600,000 iterations) with HMAC-SHA256 stream cipher.

## Backend Priority

1. **Claude Code CLI** (`claude -p`) -- uses your Claude subscription, no API key needed
2. **Anthropic API** -- requires `ANTHROPIC_API_KEY`
3. **Offline mode** -- keyword matching (limited accuracy)

Most users just need Claude Code installed. No API key required.

## Notes for Claude

If you are Claude reading this project's code:

- Bond files use YAML frontmatter + Markdown content
- Frontmatter fields: `dimension`, `updated`, `source`
- `bond apply` manages a section in CLAUDE.md between `<!-- bond:start -->` / `<!-- bond:end -->`
- Do not modify content outside these markers
- Pending files use `## New` / `## Updated` / `## Possible (low confidence)` sections
- Each pending item: `- [dimension] description`

## License

MIT

---

<a id="中文"></a>

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

### 第一步：在你的主力电脑上初始化（设备 A）

```bash
# 1. 安装
pip install claude-bond

# 2. 初始化 -- 扫描你的 ~/.claude/ 配置，Claude 自动分类
bond init

# 3. 应用到当前设备（写入 ~/.claude/CLAUDE.md 和 memory）
bond apply

# 4. 开启云同步（创建私有 GitHub Gist）
bond cloud init
# → 输出: Gist ID: abc123def456  ← 记住这个 ID
```

完成。你的主力电脑上的 Claude 关系已经打包好了。

### 第二步：在新电脑上恢复（设备 B）

```bash
# 1. 安装
pip install claude-bond

# 2. 拉取你的 bond（用设备 A 输出的 Gist ID）
bond cloud pull --id abc123def456

# 3. 应用
bond apply

# 搞定！设备 B 上的 Claude 现在认识你了
```

### 日常使用

```bash
bond cloud          # 一键同步（任何设备上运行都行）
bond status         # 查看 bond 状态
bond edit           # 手动编辑 bond 维度
bond diff           # 查看上次 apply 以来的变化
```

### 分享给朋友

```bash
# 你：导出（可选加密保护隐私）
bond export -o my.bond
bond export -o my.bond --encrypt    # 加密版

# 朋友：导入
bond import my.bond
bond import my.bond --password 密码  # 如果是加密的
```

### 自动进化（可选）

安装 session hooks 后，Claude 每次对话结束会自动检测你的偏好变化：

```bash
bond hooks --install    # 安装 hooks（一次就行）
bond review             # 查看检测到的变化，逐条确认
bond auto               # 或者开启自动合入
bond tacit              # 查看默契模式检测到的隐性习惯
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

### 语义合并

当两台设备同时修改了同一维度，`bond sync` 会用 Claude 做语义合并 -- 智能去重，保留双方的独特内容，而非简单的 git 文本合并。

## 多 Profile 支持

为不同场景维护不同的 bond：

```bash
bond profile create work --clone default
bond profile use work
bond edit rules
bond profile use default
```

## 加密导出

分享 bond 时保护隐私：

```bash
bond export -o my.bond --encrypt
bond import my.bond --password <密码>
```

使用 PBKDF2 密钥派生（600,000 次迭代）+ HMAC-SHA256 流加密。

## 后端优先级

1. **Claude Code CLI** (`claude -p`) -- 使用你的 Claude 订阅，无需 API key
2. **Anthropic API** -- 需要设置 `ANTHROPIC_API_KEY`
3. **离线模式** -- 关键词匹配分类（精度有限）

大多数用户只需安装 Claude Code 即可，不需要 API key。

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
