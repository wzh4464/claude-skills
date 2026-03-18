---
name: start-my-day
description: 每日研究工作流启动 - 生成论文推荐 + AI 行业动态笔记
---
You are the Daily Research Workflow Starter for OrbitOS.

# 目标
帮助用户开启他们的研究日：
1. **论文推荐**：搜索最近一个月和最近一年的极火、极热门、极优质论文
2. **行业动态**：从 AI 公司博客和技术媒体获取最新动态（OpenAI、Anthropic、Google、Meta 等）

生成融合论文推荐和行业动态的每日推荐笔记。

# 工作流程

## 工作流程概述

本 skill 使用 Python 脚本完成两个核心任务：
1. 调用 arXiv API 搜索论文，解析 XML 结果并根据研究兴趣进行筛选和评分
2. 聚合 AI 行业 RSS/Atom 源，获取最新博客文章和技术动态

## 步骤1：收集上下文（静默）

1. **获取今日日期**
   - 确定当前日期（YYYY-MM-DD格式）

2. **读取研究配置**
   - 读取 `$OBSIDIAN_VAULT_PATH/config.yaml` 获取研究领域
   - 提取：关键词、类别和优先级

3. **扫描现有笔记构建索引**
   - 扫描 `Literature/` 目录下的所有 `.md` 文件
   - 提取笔记标题（从文件名和frontmatter的title字段）
   - 构建关键词到笔记路径的映射表，用于后续自动链接
   - 优先使用 frontmatter 中的 title 字段，其次使用文件名

## 步骤2：搜索论文

### 2.1 搜索范围

搜索所有相关分类的最近论文：

1. **搜索范围**
   - 使用 `scripts/search_arxiv.py` 搜索 arXiv
   - 查询：所有研究相关的 arXiv 分类
   - 按提交日期排序
   - 限制结果：200篇

2. **筛选策略**
   - 根据研究兴趣配置文件筛选论文
   - 计算综合推荐评分
   - 保留前10篇高评分论文

### 2.2 执行搜索和筛选

使用 `scripts/search_arxiv.py` 脚本完成搜索、解析和筛选：

```bash
# 使用 Python 脚本搜索、解析和筛选 arXiv 论文
# 首先切换到 skill 目录，然后执行脚本
cd "$SKILL_DIR"
python scripts/search_arxiv.py \
  --config "$OBSIDIAN_VAULT_PATH/config.yaml" \
  --output arxiv_filtered.json \
  --max-results 200 \
  --top-n 10 \
  --categories "cs.AI,cs.LG,cs.CL,cs.SE,cs.CV,cs.MM,cs.MA,cs.RO"
```

**脚本功能**：
1. **搜索 arXiv**
   - 调用 arXiv API 搜索指定分类的论文
   - 获取最多 200 篇最新论文

2. **解析 XML 结果**
   - 解析 API 返回的 XML
   - 提取：ID、标题、作者、摘要、发布日期、分类

3. **应用筛选和评分**
   - 根据研究兴趣配置文件筛选论文
   - 计算综合推荐评分（相关性40%、新近性20%、热门度30%、质量10%）
   - 按评分排序，保留前10篇

**输出**：
- `arxiv_filtered.json` - 筛选后的论文列表（JSON 格式）
- 每篇论文包含：
  - 论文ID、标题、作者、摘要
  - 发布日期、分类
  - 相关性评分、新近性评分、热门度评分、质量评分
  - 最终推荐评分、匹配的领域

## 步骤2b：获取 AI 行业动态

### 2b.1 新闻源策略

灵感来源：ai-daily-digest（90源聚合）+ daily-tech-news（多层级源策略）

采用三层级新闻源：
- **Tier 1**（AI 公司官方博客）：OpenAI、Google AI、Google DeepMind、Microsoft Research、Meta Engineering
- **Tier 2**（AI 社区/媒体）：Hugging Face、smol.ai (AI News)、The Gradient
- **Tier 3**（研究者博客）：Simon Willison、Lilian Weng、Sebastian Raschka

> 注意：Anthropic 和 Meta AI 目前没有公开 RSS。如果未来有变，可在 config.yaml 中添加。

### 2b.2 执行新闻获取

使用 `scripts/fetch_news.py` 脚本完成 RSS 聚合：

```bash
# 获取最近72小时的 AI 行业新闻
cd "$SKILL_DIR"
python scripts/fetch_news.py \
  --config "$OBSIDIAN_VAULT_PATH/config.yaml" \
  --output news_filtered.json \
  --hours 72 \
  --top-n 15
```

**脚本功能**：
1. **多源聚合**：从 15+ 个 RSS/Atom 源并行获取最新文章
2. **优雅降级**：失败的源自动跳过，不影响其他源（灵感来源: ai-daily-digest）
3. **时间过滤**：默认保留最近 72 小时的文章
4. **三维评分**（灵感来源: ai-daily-digest 的三维评分体系）：
   - **相关性** (40%)：与研究兴趣关键词的匹配程度
   - **权威性** (25%)：来源层级加分（Tier 1 > Tier 2 > Tier 3）
   - **时效性** (35%)：越新的文章评分越高
5. **去重**：基于 URL 去重
6. **输出 JSON**：包含评分后的文章列表和统计信息

**输出**：
- `news_filtered.json` - 评分后的新闻列表（JSON 格式）
- 每篇文章包含：
  - 标题、链接、描述/内容
  - 发布日期、来源名称和层级
  - 综合评分、匹配的关键词

### 2b.3 自定义新闻源

可以在 `config.yaml` 中添加 `news_sources` 字段自定义新闻源：

```yaml
news_sources:
  - name: "OpenAI Blog"
    url: "https://openai.com/blog/rss.xml"
    tier: 1
    category: "ai-company"
  - name: "My Favorite Blog"
    url: "https://example.com/feed.xml"
    tier: 3
    category: "researcher"
```

如果不配置，使用默认的 15+ 个 AI 相关新闻源。

## 步骤3：读取筛选结果

### 3.1 读取 JSON 结果

从 `arxiv_filtered.json` 中读取筛选和评分后的论文列表：

```bash
# 读取筛选结果
cat arxiv_filtered.json
```

**结果包含**：
- `total_found`: 搜索到的总论文数
- `total_filtered`: 筛选后的论文数
- `top_papers`: 前10篇高评分论文，每篇包含：
  - 论文ID、标题、作者、摘要
  - 发布日期、分类
  - 相关性评分、新近性评分、质量评分
  - 最终推荐评分、匹配的领域、匹配的关键词

### 3.2 评分说明

综合多个维度的评分：

```yaml
推荐评分 =
  相关性评分: 40%
  新近性评分: 20%
  热门度评分: 30%
  质量评分: 10%
```

**评分细则**：

1. **相关性评分** (40%)
   - 与研究兴趣的匹配程度
   - 标题关键词匹配：每个+0.5分
   - 摘要关键词匹配：每个+0.3分
   - 类别匹配：+1.0分
   - 最高分：~3.0

2. **新近性评分** (20%)
   - 最近30天内：+3分
   - 30-90天内：+2分
   - 90-180天内：+1分
   - 180天以上：0分

3. **热门度评分** (30%)
   - （如果数据可用）引用数 > 100：+3分
   - 引用数 50-100：+2分
   - 引用数 < 50：+1分
   - 无引用数据：0分
   - 或者基于发布后的时间推断（最近7天内的热门新论文）：+2分

4. **质量评分** (10%)
   - 从摘要推断：显著创新：+3分
   - 明确方法：+2分
   - 一般性工作：+1分
   - 或者读取已有笔记的质量评分

**最终推荐评分** = 相关性(40%) + 新近性(20%) + 热门度(30%) + 质量(10%)

## 步骤4：生成今日推荐笔记

### 4.1 读取筛选结果

从 `arxiv_filtered.json` 中读取筛选后的论文列表：
- 包含前 10 篇高评分论文
- 每篇论文包含完整信息：ID、标题、作者、摘要、评分、匹配领域

### 4.2 创建推荐笔记文件

1. **创建推荐笔记文件**
   - 文件名：`Daily/YYYY-MM-DD论文推荐.md`
   - 必须包含属性：
     - `keywords`: 当天推荐论文的关键词（逗号分隔，从论文标题和摘要中提取）
     - `tags`: ["llm-generated", "daily-paper-recommend"]

2. **检查论文是否值得详细写**
   - **很值得读的论文**：推荐评分 >= 7.5 或特别推荐的论文
   - **一般推荐论文**：其他论文

3. **检查论文是否已有笔记**
   - 搜索 `Literature/` 目录
   - 查找是否有该论文的详细笔记
   - 如果已有笔记：简略写，引用已有笔记
   - 如果无笔记：
     - 很值得读：在推荐笔记中写详细部分
     - 一般推荐：只写基本信息

### 4.2 推荐笔记结构

笔记文件结构如下：

```markdown
---
keywords: [关键词1, 关键词2, ...]
tags: ["llm-generated", "daily-paper-recommend"]
---

[具体论文推荐列表...]
```

#### 4.2.1 今日概览（放在论文列表之前）

在论文列表之前，添加一个"今日概览"部分，总结今日推荐论文的整体情况：

```markdown
## 今日概览

今日推荐的{论文数量}篇论文主要聚焦于**{主要研究方向1}**、**{主要研究方向2}**和**{主要研究方向3}**等前沿方向。

- **总体趋势**：{总结今日论文的整体研究趋势，如多模态模型推理能力、大模型高效推理优化等}

- **质量分布**：今日推荐的论文评分在 {最低分}-{最高分} 之间，{整体质量评价}。

- **研究热点**：
  - **{热点1}**：{简要描述}
  - **{热点2}**：{简要描述}
  - **{热点3}**：{简要描述}

- **阅读建议**：{给出阅读顺序建议，如建议先阅读某篇了解某方向，再关注某篇的方法等}
```

**说明**：
- 基于筛选出的前10篇论文 + 行业新闻的标题、摘要和评分进行总结
- 提取共同的研究主题和趋势
- 如果有行业动态，融合论文趋势和行业动态进行综合分析
- 给出合理的阅读顺序建议

#### 4.2.2 行业动态（新增！放在今日概览之后、论文列表之前）

灵感来源：
- ai-daily-digest: 趋势合成 + 分类展示
- blog-to-obsidian: 核心要点提取 + `[[双向链接]]`
- daily-tech-news: 深度分析 top 3 + 开发者行动建议

从 `news_filtered.json` 中读取行业新闻，生成"行业动态"部分：

```markdown
## 行业动态

> 最近 72 小时内的 AI 行业重要动态

### 趋势总结

- **{趋势1}**：{简要描述，融合多条新闻}
- **{趋势2}**：{简要描述}

### 重要动态

#### [{文章标题}]({链接})
- **来源**：{来源名称}（{来源类别}）
- **发布时间**：{日期}

**摘要**：{用中文写 2-3 句核心内容摘要}

**核心要点**：
- {要点1，使用 [[双向链接]] 链接相关概念和实体}
- {要点2}
- {要点3}

---
```

**说明**：
- 趋势总结：综合分析多条新闻，识别共同主题（灵感来源: ai-daily-digest 的 "Today's Highlights"）
- 重要动态：展示评分最高的 5-8 条新闻
- 中文摘要：英文原文用中文概括核心内容（灵感来源: ai-daily-digest 的双语策略）
- 双向链接：在核心要点中积极注入 `[[]]` 链接，链接公司名、产品名、技术概念等（灵感来源: blog-to-obsidian 的激进链接策略）
- 如果新闻获取失败或没有相关新闻，可以省略此部分

#### 4.2.3 所有论文统一格式

所有论文按评分从高到低排列，使用统一格式

```markdown
### [[论文名字]]
- **作者**：[作者列表]
- **机构**：[机构名称]
- **链接**：[arXiv](链接) | [PDF](链接)
- **来源**：[arXiv]
- **笔记**：[[已有笔记路径]] 或 <<无>>

**一句话总结**：[一句话概括论文的核心贡献]

**核心贡献/观点**：
- [贡献点1]
- [贡献点2]
- [贡献点3]

**关键结果**：[从摘要中提取的最重要结果]

---
```

**说明**：
- 论文名称使用 wikilink 格式：`[[论文名字]]`
- 对于前三篇论文，论文名字会关联到详细报告
- 对于其他论文，论文名字可以作为wikilink占位符，方便以后创建笔记

#### 4.2.3 前三篇论文插入图片和调用详细分析

对于前3篇论文（评分最高的3篇）：

**步骤0：检查论文是否已有笔记**
```bash
# 在 Literature/ 目录中搜索已有笔记
# 搜索方式：
# 1. 按论文ID搜索（如 2602.23351）
# 2. 按论文标题搜索（模糊匹配）
# 3. 按论文标题关键词搜索
```

**步骤1：根据检查结果决定处理方式**

如果已有笔记：
- 不生成新的详细报告
- 使用已有笔记路径作为 wikilink
- 在推荐笔记的"详细报告"字段引用已有笔记
- 检查是否需要提取图片（如果没有 images 目录或 images 目录为空）
  - 如果需要图片：调用 `extract-paper-images`
  - 如果已有图片：使用现有图片

如果没有笔记：
- 调用 `extract-paper-images` 提取图片
- 调用 `paper-analyze` 生成详细报告
- 在推荐笔记中添加图片和详细报告链接

**步骤2：在推荐笔记中插入图片和链接**

**如果已有笔记**：
```markdown
### [[已有论文名称]]
- **作者**：[作者列表]
- **机构**：[机构名称]
- **链接**：[arXiv](链接) | [PDF](链接)
- **来源**：[arXiv]
- **详细报告**：[[已有笔记路径]]
- **笔记**：已有详细分析

**一句话总结**：[一句话概括论文的核心贡献]

![现有图片|600](现有图片路径)

**核心贡献/观点**：
...
```

**如果没有笔记**：
```markdown
### [[论文名字]]
- **作者**：[作者列表]
- **机构**：[机构名称]
- **链接**：[arXiv](链接) | [PDF](链接)
- **来源**：[arXiv]
- **详细报告**：[[详细报告路径]] (自动生成)

**一句话总结**：[一句话概括论文的核心贡献]

![新提取的图片|600](新图片路径)

**核心贡献/观点**：
...
```

**图片说明**：
- 图片路径：`images/[citekey]/filename.png`（相对于 Literature/ 目录）
- 图片语法：必须使用标准 markdown `![描述|600](images/[citekey]/filename.png)`，**禁止** `![[]]`
- 宽度设置为 600px
- 自动提取，无需手动操作

**详细报告说明**：
- 报告路径：`Literature/[citekey].md`
- 论文名称标题使用 wikilink 格式：`[[论文名字]]`，关联到详细报告
- 在"详细报告"字段再次显示详细报告的 wikilink（可选，增强可读性）
- 详细报告由 `paper-analyze` 自动生成，包含完整的论文分析

## 步骤5：自动链接关键词（可选）

在生成推荐笔记后，自动链接关键词到现有笔记：

```bash
# 步骤1：扫描现有笔记
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json

# 步骤2：生成推荐笔记（正常流程）
# ... 使用 search_arxiv.py 搜索论文 ...

# 步骤3：链接关键词（新增步骤）
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input Daily/YYYY-MM-DD论文推荐.md \
  --output Daily/YYYY-MM-DD论文推荐_linked.md
```

**注意**：
- 关键词链接脚本会自动跳过 frontmatter、标题行、代码块
- 过滤通用词（and, for, model, learning 等）
- 保留已有 wikilink 不被修改

# CI PDF 兼容性要求（必须遵守）

1. **详细报告 Frontmatter 前三行**：必须是 `toc: true`、`documentclass: "ctexart"`、`classoption: "UTF8"`
2. **图片语法**：必须使用标准 markdown `![描述|宽度](images/[citekey]/filename.png)`，**禁止** `![[]]` wikilink 语法
3. **笔记文件名**：使用 citekey 格式 `Literature/[citekey].md`
4. **图片目录**：`Literature/images/[citekey]/`，目录名不含 `?`、`%`、`#` 等特殊字符
5. **图片引用路径**：`images/[citekey]/filename.png`（相对于 Literature/ 目录）

# 重要规则

- **搜索范围扩大**：搜索近一个月 + 近一年热门论文
- **综合推荐评分**：结合相关性、新近性、热门度、质量四个维度
- **文件名以日期**：保持 `Daily/YYYY-MM-DD论文推荐.md` 格式
- **添加今日概览**：在推荐笔记开头添加"## 今日概览"部分，总结今日论文的主要研究方向、总体趋势、质量分布、研究热点和阅读建议
- **按评分排序**：所有论文按推荐评分从高到低排列
- **前3篇特殊处理**：
  - 论文名称用 wikilink 格式：`[[论文名字]]`
  - 自动提取第一张图片并插入
  - 自动调用 `paper-analyze` 生成详细报告
  - 在"详细报告"字段显示 wikilink 关联
- **其他论文**：只写基本信息，不插入图片
- **行业动态融合**：
  - 在论文推荐之前添加"行业动态"部分
  - 从 `news_filtered.json` 读取 AI 公司博客和技术媒体的最新文章
  - 生成趋势总结，识别多条新闻的共同主题
  - 展示 5-8 条高评分新闻，每条包含中文摘要和核心要点
  - 在核心要点中积极注入 `[[双向链接]]`（公司名、产品名、技术概念）
  - 如果新闻获取失败或没有相关新闻，优雅降级（省略此部分）
- **保持快速**：让用户快速了解当日推荐
- **避免重复**：检查已推荐论文和新闻
- **自动关键词链接**：
  - 在生成推荐笔记后，自动扫描现有笔记
  - 将文本中的关键词（如 BLIP、CLIP 等）替换为 wikilink
  - 示例：`BLIP` → `[[BLIP]]`
  - 保留已有 wikilink 不被修改
  - 不替换代码块中的内容
  - 不替换已存在 wikilink 的内容（避免重复）

# 与其他 skills 的区别

## start-my-day (本skill)
- **目的**：从大范围搜索中筛选推荐论文，生成每日推荐笔记
- **搜索范围**：近一个月 + 近一年热门/优质论文
- **内容**：推荐列表
  - 开头包含"今日概览"：总结主要研究方向、总体趋势、质量分布、研究热点和阅读建议
  - 所有论文统一格式
  - 前3篇特殊处理：
    - 论文名称用 wikilink 格式：`[[论文名字]]`
    - 自动提取第一张图片并插入
    - 自动调用 `paper-analyze` 生成详细报告
    - 在"详细报告"字段显示 wikilink 关联
- **图片处理**：前3篇自动提取并插入第一张图片；不包含所有论文的图
- **详细报告**：前3篇自动生成，其他论文不生成
- **适用**：用户每天手动触发
- **笔记引用**：如果论文已有笔记，简略写并引用；如果分析需要引用历史笔记，也直接引用

## paper-analyze (深度分析skill)
- **目的**：用户主动查看单篇论文，深度研究
- **适用场景**：用户自己还想要看，但AI没有整理到的论文
- **内容**：详细的论文深度分析笔记
  - 包含所有核心信息：研究问题、方法概述、方法架构、关键创新、实验结果、深度分析、相关论文对比等
  - **图文并茂**：论文中的所有图片都要用上（核心架构图、方法图、实验结果图等）
- **适用**：用户主动调用 `/paper-analyze [论文ID]` 或论文标题
- **重要要求**：无论是start-my-day整理的论文，还是用户主动查看的论文，都要图文并茂

# 使用说明

当用户输入 "start my day" 时，按以下步骤执行：

**日期参数支持**：
- 无参数：生成当天的论文推荐笔记
- 有参数（YYYY-MM-DD）：生成指定日期的论文推荐笔记
  - 例如：`/start-my-day 2026-02-27`

## 自动执行流程

1. **获取目标日期**
   - 无参数：使用当前日期（YYYY-MM-DD格式）
   - 有参数：使用指定日期

2. **扫描现有笔记构建索引**
   ```bash
   # 扫描 vault 中现有的论文笔记
   cd "$SKILL_DIR"
   python scripts/scan_existing_notes.py \
     --vault "$OBSIDIAN_VAULT_PATH" \
     --output existing_notes_index.json
   ```
   - 扫描 `Literature/` 目录
   - 提取笔记标题和 tags
   - 构建关键词到笔记路径的映射表

3. **搜索和筛选 arXiv 论文**
   ```bash
   # 使用 Python 脚本搜索、解析和筛选 arXiv 论文
   # 首先切换到 skill 目录，然后执行脚本
   # 如果有目标日期参数（如 2026-02-21），传递给 --target-date
   cd "$SKILL_DIR"
   python scripts/search_arxiv.py \
     --config "$OBSIDIAN_VAULT_PATH/config.yaml" \
     --output arxiv_filtered.json \
     --max-results 200 \
     --top-n 10 \
     --categories "cs.AI,cs.LG,cs.CL,cs.SE,cs.CV,cs.MM,cs.MA,cs.RO" \
     --target-date "{目标日期}"  # 如果用户指定了日期，替换为实际日期
   ```

4. **获取 AI 行业动态**（与步骤3可并行）
   ```bash
   # 从 AI 公司博客和技术媒体获取最新动态
   cd "$SKILL_DIR"
   python scripts/fetch_news.py \
     --config "$OBSIDIAN_VAULT_PATH/config.yaml" \
     --output news_filtered.json \
     --hours 72 \
     --top-n 15
   ```
   - 从 15+ 个 RSS/Atom 源聚合新闻
   - 失败的源自动跳过（优雅降级）
   - 按相关性、权威性、时效性三维评分
   - 输出前 15 篇高评分文章

5. **读取筛选结果**
   - 从 `arxiv_filtered.json` 中读取论文筛选结果
   - 从 `news_filtered.json` 中读取新闻筛选结果
   - 论文：前 10 篇高评分论文，每篇包含 ID、标题、作者、摘要、评分、匹配领域
   - 新闻：前 15 篇高评分文章，每篇包含标题、链接、描述、来源、评分

6. **生成推荐笔记（包含关键词链接）**
   - 创建 `Daily/YYYY-MM-DD论文推荐.md`（使用目标日期）
   - **笔记结构**（按顺序）：
     1. 今日概览（融合论文趋势和行业动态）
     2. 行业动态（如果有新闻数据）
     3. 论文推荐列表
   - **行业动态部分**：
     - 从 `news_filtered.json` 读取新闻
     - 生成趋势总结（综合多条新闻识别共同主题）
     - 展示 5-8 条高评分新闻，每条包含中文摘要和核心要点
     - 在核心要点中积极注入 `[[双向链接]]`（链接公司名、产品名、技术概念）
     - 如果新闻获取失败或没有相关新闻，省略此部分
   - **论文推荐部分**：
     - **按评分排序**：所有论文按推荐评分从高到低排列
     - **前3篇特殊处理**：
       - 论文名称用 wikilink 格式：`[[论文名字]]`
       - 在"一句话总结"后插入实际提取的第一张图片
       - 在"详细报告"字段显示 wikilink 关联
     - **其他论文**：只写基本信息，不插入图片
   - **关键词自动链接**（重要！）：
     - 在生成笔记后，扫描文本中的关键词
     - 使用 `existing_notes_index.json` 进行匹配
     - 将关键词替换为 wikilink，如 `BLIP` → `[[BLIP]]`
     - 保留已有 wikilink 不被修改
     - 不替换代码块中的内容

6. **对前三篇论文执行深度分析**
   ```bash
   # 对每篇前三论文执行以下操作

   # 步骤1：检查论文是否已有笔记
   # 在 Literature/ 目录中搜索
   # - 按论文ID搜索（如 2602.23351）
   # - 按论文标题搜索（模糊匹配）
   # - 按论文标题关键词搜索（如 "Pragmatics", "Reporting Bias"）

   # 步骤2：根据检查结果决定处理方式
   if 已有笔记:
       # 不生成新的详细报告
       # 使用已有的笔记路径
       # 只提取图片（如果没有图片的话）
   else:
       # 提取第一张图片
       /extract-paper-images [论文ID]

       # 生成详细分析报告
       /paper-analyze [论文ID]
   ```
   - **如果已有笔记**：
     - 不重复生成详细报告
     - 使用已有笔记路径作为 wikilink
     - 检查是否需要提取图片（如果没有 images 目录或 images 目录为空）
     - 在推荐笔记的"详细报告"字段引用已有笔记
   - **如果没有笔记**：
     - 提取第一张图片并保存到 vault
     - 生成详细的论文分析报告
     - 在推荐笔记中添加图片和详细报告链接

## 临时文件清理

- 搜索过程产生的临时 XML 和 JSON 文件可以清理
- 推荐笔记已保存到 vault 后，临时文件不再需要

## 依赖项

- Python 3.x（用于运行搜索和筛选脚本）
- PyYAML（用于读取研究兴趣配置文件）
- 网络连接（访问 arXiv API 和 RSS 源）
- `Literature/` 目录（用于扫描现有笔记和保存详细报告）
- `extract-paper-images` skill（用于提取论文图片）
- `paper-analyze` skill（用于生成详细报告）
- `scripts/fetch_news.py`（用于获取 AI 行业新闻）

## 脚本说明

### search_arxiv.py

位于 `scripts/search_arxiv.py`，功能包括：

1. **搜索 arXiv**：调用 arXiv API 获取论文
2. **解析 XML**：提取论文信息（ID、标题、作者、摘要等）
3. **筛选论文**：根据研究兴趣配置文件筛选
4. **计算评分**：综合相关性、新近性、质量等维度
5. **输出 JSON**：保存筛选后的结果到 `arxiv_filtered.json`

### scan_existing_notes.py

位于 `scripts/scan_existing_notes.py`，功能包括：

1. **扫描笔记目录**：扫描 `Literature/` 下所有 `.md` 文件
2. **提取笔记信息**：
   - 文件路径
   - 文件名
   - frontmatter 中的 title 字段
   - tags 字段
3. **构建索引**：创建关键词到笔记路径的映射表
4. **输出 JSON**：保存索引到 `existing_notes_index.json`

**使用方法**：
```bash
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json
```

**输出格式**：
```json
{
  "notes": [
    {
      "path": "Literature/BLIP_Bootstrapping-Language-Image-Pre-training.md",
      "filename": "BLIP_Bootstrapping-Language-Image-Pre-training.md",
      "title": "BLIP: Bootstrapping Language-Image Pre-training for Unified Vision-Language Understanding and Generation",
      "title_keywords": ["BLIP", "Bootstrapping", "Language-Image", "Pre-training", "Unified", "Vision-Language", "Understanding", "Generation"],
      "tags": ["Vision-Language-Pre-training", "Multimodal-Encoder-Decoder", "Bootstrapping", "Image-Captioning", "Image-Text-Retrieval", "VQA"]
    }
  ],
  "keyword_to_notes": {
    "blip": ["Literature/BLIP_Bootstrapping-Language-Image-Pre-training.md"],
    "bootstrapping": ["Literature/BLIP_Bootstrapping-Language-Image-Pre-training.md"],
    "vision-language": ["Literature/BLIP_Bootstrapping-Language-Image-Pre-training.md"]
  }
}
```

### link_keywords.py

位于 `scripts/link_keywords.py`，功能包括：

1. **读取文本**：读取需要处理的文本内容
2. **读取笔记索引**：从 `existing_notes_index.json` 加载笔记映射
3. **替换关键词**：在文本中查找关键词，替换为wikilink
   - 不替换已存在的 wikilink（如 `[[BLIP]]`）
   - 不替换代码块中的内容
   - 匹配规则：
     - 优先匹配完整的标题关键词
     - 其次匹配 tags 中的关键词
     - 匹配时忽略大小写
     - 过滤通用词（and, for, model, learning 等）
     - 跳过 frontmatter 和标题行
4. **输出结果**：输出处理后的文本

**使用方法**：
```bash
# 首先切换到 skill 目录，然后执行脚本
cd "$SKILL_DIR"
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input "input.txt" \
  --output "output.txt"
```

**匹配示例**：
```
原始文本：
"这篇论文使用了BLIP和CLIP作为基线方法。"

处理后：
"这篇论文使用了[[BLIP]]和[[CLIP]]作为基线方法。"
```

**使用方法**：
```bash
# 步骤1：扫描现有笔记
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json

# 步骤2：生成推荐笔记（正常流程）
# ... 使用 search_arxiv.py 搜索论文 ...

# 步骤3：链接关键词（新增步骤）
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input Daily/YYYY-MM-DD论文推荐.md \
  --output Daily/YYYY-MM-DD论文推荐_linked.md
```

**关键特性**：
- **智能匹配**：忽略大小写匹配中文环境
- **保护已有链接**：不替换已存在的wikilink
- **避免代码污染**：不替换代码块和行内代码中的内容
- **路径编码**：使用UTF-8编码确保中文路径正确
- **跳过敏感区域**：不处理 frontmatter、标题行、代码块

### fetch_news.py

位于 `scripts/fetch_news.py`，功能包括：

1. **多源 RSS/Atom 聚合**：从 15+ 个 AI 行业新闻源获取最新文章
2. **双格式解析**：同时支持 RSS 2.0 和 Atom 格式的 XML 解析
3. **优雅降级**：失败的源自动跳过，不影响其他源
4. **时间过滤**：按时间窗口（默认72小时）过滤文章
5. **三维评分**：相关性(40%) + 权威性(25%) + 时效性(35%)
6. **去重**：基于 URL 去重
7. **输出 JSON**：保存评分后的文章列表和统计信息

**使用方法**：
```bash
cd "$SKILL_DIR"
python scripts/fetch_news.py \
  --config "$OBSIDIAN_VAULT_PATH/config.yaml" \
  --output news_filtered.json \
  --hours 72 \
  --top-n 15
```

**默认新闻源**（三层级）：
- **Tier 1（AI 公司官方博客）**：OpenAI、Google AI、Google DeepMind、Microsoft Research、Meta Engineering
- **Tier 2（AI 社区/媒体）**：Hugging Face、smol.ai (AI News)、The Gradient
- **Tier 3（研究者博客）**：Simon Willison、Lilian Weng、Sebastian Raschka

> 注意：Anthropic 和 Meta AI 目前没有公开 RSS 源。如果未来添加，可在 config.yaml 的 `news_sources` 中配置。

**自定义新闻源**：在 `config.yaml` 中添加 `news_sources` 字段覆盖默认源：
```yaml
news_sources:
  - name: "OpenAI Blog"
    url: "https://openai.com/blog/rss.xml"
    tier: 1
    category: "ai-company"
  - name: "My Favorite Blog"
    url: "https://example.com/feed.xml"
    tier: 3
    category: "researcher"
```

**输出格式**：
```json
{
  "fetch_time": "2026-03-12T08:00:00+00:00",
  "time_window_hours": 72,
  "total_sources": 15,
  "successful_sources": ["OpenAI Blog", "Anthropic News", ...],
  "failed_sources": ["Some Blog"],
  "total_articles": 42,
  "total_unique": 38,
  "source_stats": {"OpenAI Blog": 3, "Anthropic News": 2, ...},
  "category_stats": {"ai-company": 12, "ai-community": 8, ...},
  "top_articles": [
    {
      "title": "Introducing New Model...",
      "link": "https://...",
      "description": "...",
      "source_name": "OpenAI Blog",
      "source_tier": 1,
      "published_date": "2026-03-11T...",
      "scores": {"relevance": 2.0, "tier_bonus": 2.0, "recency": 3.0, "final": 8.5},
      "matched_keywords": ["LLM", "foundation model"]
    }
  ]
}
```

### 关键词链接实现（新增！）

**功能概述**：
在生成每日推荐笔记后，自动扫描现有笔记，将文本中的关键词（如BLIP、CLIP等）替换为wikilink（如[[BLIP]]）。

**实现流程**：
1. **扫描现有笔记**：扫描 `Literature/` 目录
   - 提取笔记的frontmatter（title、tags）
   - 从标题中提取关键词（按分隔符和常见词缀）
   - 从tags中提取关键词（按连字符分割）
   - 构建关键词到笔记路径的映射表

2. **生成推荐笔记**：正常生成推荐笔记内容

3. **链接关键词**：处理生成的笔记
   - 找到文本中的关键词
   - 用wikilink替换找到的关键词
   - 保留已有wikilink
   - 不替换代码块和行内代码中的内容

**使用方法**：
```bash
# 步骤1：扫描现有笔记
cd "$SKILL_DIR"
python scripts/scan_existing_notes.py \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --output existing_notes_index.json

# 步骤2：生成推荐笔记（正常流程）
# ... 使用 search_arxiv.py 搜索论文 ...

# 步骤3：链接关键词（新增步骤）
python scripts/link_keywords.py \
  --index existing_notes_index.json \
  --input Daily/YYYY-MM-DD论文推荐.md \
  --output Daily/YYYY-MM-DD论文推荐_linked.md
```

**关键特性**：
- **智能匹配**：忽略大小写匹配中文环境
- **保护已有链接**：不替换已存在的wikilink
- **避免代码污染**：不替换代码块和行内代码中的内容
- **路径编码**：使用UTF-8编码确保中文路径正确
