# claude-bond: Design Spec

> 打包你和 Claude 的关系，让 Claude 在任何设备都认识你

## 1. 核心理念

claude-bond 打包的不是 Claude 的灵魂，而是**用户和 Claude 之间的关系**。这个关系包含 Claude 对用户的认知、用户教会 Claude 的规矩、双方形成的沟通风格、以及跨对话积累的记忆。

核心价值：用户换一台电脑，运行一个命令，Claude 就"认识你了"。

## 2. 目标场景

| 场景 | 描述 |
|------|------|
| 跨设备同步 | 公司电脑和家里电脑的 Claude 保持一致 |
| 身份打包/分享 | 将调教好的 Claude 关系打包为文件，分享给他人或社区 |
| 跨平台迁移 | 在 Claude Code、Claude Web、其他 AI 工具间保持一致的体验 |

## 3. 产品形态

CLI 工具 + Claude Code Hook，Python 技术栈。

- CLI 保证通用性（导出、导入、分享、迁移）
- Hook 保证无感体验（自动应用、自动进化）

## 4. Bond 维度（MVP）

| 维度 | 文件 | 内容 | 来源 |
|------|------|------|------|
| 用户画像 | identity.md | 角色、技术水平、知识背景 | 扫描 + 对话 |
| 行为规矩 | rules.md | 用户纠正/确认过的所有偏好 | 扫描 |
| 沟通风格 | style.md | 语言、语气、回复长度、解释深度 | 对话 |
| 记忆 | memory.md | 跨对话积累的事实性记忆 | 扫描 |

### 后续版本扩展维度

- 默契模式 — 隐性沟通习惯（AI 自动学习）
- 技术偏好 — 框架、代码风格、架构偏好
- 工作上下文 — 项目、团队、deadline
- 工具链配置 — MCP servers、hooks、skills

## 5. 文件格式

### 5.1 日常格式：Markdown 文件集

```
~/.claude-bond/
  ├── identity.md       # 用户画像
  ├── rules.md          # 行为规矩
  ├── style.md          # 沟通风格
  ├── memory.md         # 关键记忆
  ├── bond.yaml         # 元信息
  └── pending/          # 待确认的变化
      └── YYYY-MM-DD.md # 每日检测到的变化
```

每个维度文件统一 frontmatter：

```markdown
---
dimension: identity
updated: 2026-03-29
source: [scan, interview]
---

- 数据科学家，专注 NLP 方向
- Python 为主力语言，熟悉 Go
```

### 5.2 元信息：bond.yaml

```yaml
version: "0.1.0"
created: 2026-03-29
updated: 2026-03-29
claude_model: opus
dimensions: [identity, rules, style, memory]
checksum: sha256:...
```

### 5.3 导出格式：.bond 文件

ZIP 包，包含上述所有 Markdown 文件和 bond.yaml。用于分享和迁移。

## 6. CLI 命令

| 命令 | 功能 | 详细说明 |
|------|------|---------|
| `bond init` | 初始化 bond | 扫描 ~/.claude/ 提取已有信息，Claude 整理归类，AI 对话补充缺失维度 |
| `bond apply` | 应用 bond | 将 bond 文件转化为 CLAUDE.md + memory 文件写入 ~/.claude/ |
| `bond export` | 导出 | 将 ~/.claude-bond/ 打包成 .bond 文件 |
| `bond import <file>` | 导入 | 从 .bond 文件解压到 ~/.claude-bond/ 并执行 apply |
| `bond sync` | 同步 | Git push/pull 一键同步（需先配置 remote） |
| `bond review` | 审核变化 | 展示 pending/ 中的变化，逐条确认或丢弃 |
| `bond auto` | 自动合入 | 开启/关闭自动合入模式（跳过审核） |

## 7. 提取引擎（bond init）

### 7.1 第一步：自动扫描

扫描 `~/.claude/` 下的以下来源：

| 来源 | 提取内容 |
|------|---------|
| `CLAUDE.md`（全局 + 项目级） | 行为规矩、技术偏好 |
| `memory/` 目录下所有 .md 文件 | 记忆、用户画像、项目上下文 |
| `settings.json` | 工具配置、语言偏好 |
| 各项目的 `.claude/` 目录 | 项目级记忆和规则 |

扫描结果交给 Claude API 做结构化整理 — 将散落在不同文件里的信息归类到 identity / rules / style / memory 四个维度。

### 7.2 第二步：AI 补充对话

扫描完成后，Claude 审视提取结果，识别缺失维度，发起 3-5 个针对性问题。

交互示例：

```
📋 已从你的配置中提取到：
  ✓ 身份认知 — 3 条信息
  ✓ 行为规矩 — 8 条规则
  ✗ 沟通风格 — 信息不足
  ✓ 记忆 — 12 条

我想再确认几个问题来补全你的 bond：

1. 你希望我回复用中文还是英文？还是看情况？
2. 你喜欢简短直接的回复，还是详细解释？
```

问完后生成完整的 bond 文件集到 `~/.claude-bond/`。

## 8. 应用引擎（bond apply）

将 bond 文件集转化为 Claude Code 可识别的配置：

1. 读取 identity.md / rules.md / style.md → 合成为 `~/.claude/CLAUDE.md` 中的一个 section（不覆盖用户已有内容，追加 `## Bond` section）
2. 读取 memory.md → 写入 `~/.claude/memory/` 目录下对应的 memory 文件

应用时由 Claude API 做"消化" — 不是机械拼接，而是理解后生成自然的 CLAUDE.md 内容。

## 9. 进化机制

### 9.1 自动检测

Claude Code session 结束时，`post-session` hook 触发：

1. Hook 扫描 `~/.claude/` 目录下 memory 文件和 CLAUDE.md 的变化（对比上次快照）
2. 将变化内容发送给 Claude API，分析是否涉及 bond 维度更新：
   - 新规矩（用户纠正了行为）
   - 身份更新（用户提到角色/背景变化）
   - 新记忆（重要事实）
   - 风格微调（沟通模式变化）
3. 检测到的变化写入 `~/.claude-bond/pending/YYYY-MM-DD.md`
4. 首次 apply 时保存 `~/.claude-bond/.snapshot/` 作为基线，后续每次 hook 对比增量

**约束说明**：Claude Code hook 无法直接访问对话内容。进化机制通过检测 `~/.claude/` 目录下文件的增量变化（memory 新增、CLAUDE.md 修改等）间接感知对话影响，而非直接读取对话记录。

### 9.2 变化审核

pending 文件格式：

```markdown
---
date: 2026-03-29
session_count: 3
---

## 新增

- [rules] 用户说"别给我写测试，我自己写"
- [memory] deer-flow 项目已部署上线

## 更新

- [identity] 用户提到转岗做了后端（原：数据科学家）

## 可能的变化（低置信度）

- [style] 用户连续 3 次用极短回复，可能偏好更简洁
```

### 9.3 合入方式

- `bond review`：逐条展示，用户确认（y）或丢弃（n）
- `bond auto`：开启自动模式，所有变化自动合入（高置信度直接合入，低置信度标记但保留）
- 默认模式：pending 累积，不主动打扰，用户想审核时再审核

## 10. 同步机制（MVP）

基于 Git：

```bash
bond sync --init git@github.com:user/my-bond.git  # 首次配置 remote
bond sync                                          # 日常推拉
```

内部实现：
1. 检查 `~/.claude-bond/` 是否为 git 仓库，不是则 `git init`
2. `git add -A && git commit -m "bond update YYYY-MM-DD"`
3. `git pull --rebase && git push`

冲突处理：如果两台设备同时修改了同一维度，用 Claude API 做语义合并（而非 git 文本合并）。

云同步留 v2。

## 11. 安全考虑

- bond 文件包含个人信息，默认 `.gitignore` 排除 `.bond` 导出文件
- `bond sync` 时警告用户使用私有仓库
- 导出的 .bond 文件不包含 API key、token 等敏感信息（扫描时自动过滤）
- 后续版本支持加密导出（AES-256）

## 12. 技术栈

| 组件 | 选型 |
|------|------|
| CLI 框架 | Typer（基于 Click，类型提示友好） |
| Claude API | anthropic Python SDK |
| 文件打包 | Python zipfile 标准库 |
| Git 操作 | subprocess 调用 git 命令 |
| 配置管理 | PyYAML |
| 分发 | pip（PyPI） |

## 13. 项目结构

```
claude-bond/
├── pyproject.toml
├── src/
│   └── claude_bond/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI 入口
│       ├── commands/
│       │   ├── init.py         # bond init
│       │   ├── apply.py        # bond apply
│       │   ├── export_cmd.py   # bond export
│       │   ├── import_cmd.py   # bond import
│       │   ├── sync.py         # bond sync
│       │   ├── review.py       # bond review
│       │   └── auto.py         # bond auto
│       ├── extractor/
│       │   ├── scanner.py      # ~/.claude/ 扫描器
│       │   └── interviewer.py  # AI 补充对话
│       ├── applier/
│       │   └── applier.py      # bond → ~/.claude/ 转换
│       ├── evolve/
│       │   ├── detector.py     # session 变化检测
│       │   └── merger.py       # pending 合入逻辑
│       ├── sync_engine/
│       │   └── git_sync.py     # Git 同步
│       ├── models/
│       │   └── bond.py         # Bond 数据模型
│       └── utils/
│           ├── claude_api.py   # Claude API 封装
│           ├── file_ops.py     # 文件操作
│           └── security.py     # 敏感信息过滤
├── hooks/
│   ├── session-start.sh        # apply hook
│   └── session-end.sh          # evolve hook
└── tests/
    ├── test_scanner.py
    ├── test_interviewer.py
    ├── test_applier.py
    ├── test_detector.py
    └── test_sync.py
```

## 14. MVP 范围

### 包含

- `bond init`（扫描 + AI 对话）
- `bond apply`（bond → ~/.claude/）
- `bond export` / `bond import`（.bond 文件打包/解包）
- `bond sync`（Git 同步）
- `bond review` / `bond auto`（变化审核）
- session-start hook（自动 apply）
- session-end hook（自动检测变化）
- 敏感信息过滤

### 不包含

- 云同步（v2）
- 默契模式自动学习（v2）
- 技术偏好 / 工作上下文 / 工具链配置维度（v2）
- 加密导出（v2）
- 灵魂社区/市场（v3）
- Web UI（v3）

## 15. 成功标准

1. 用户在设备 A 运行 `bond init`，在设备 B 运行 `bond sync && bond apply`，设备 B 上的 Claude 表现出与设备 A 一致的行为
2. Bond 进化机制能自动捕捉 >80% 的显式偏好变化（用户纠正/确认）
3. 整个流程（init → sync → apply）不超过 2 分钟
4. 导出的 .bond 文件可以被另一个用户导入并获得有意义的体验提升
