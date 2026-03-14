# LaTeX 论文翻译 - 快速开始

## 🚀 5分钟快速使用

### 步骤 1: 配置 API

在你的 LaTeX 项目根目录创建 `.env` 文件：

```bash
API_BASE_URL=https://api.chatanywhere.org/v1
API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-4o
```

### 步骤 2: 调用 Skill

在 Claude Code 中，进入你的 LaTeX 项目目录，然后输入：

```
/translate-latex
```

或者直接说：

```
帮我把这个 LaTeX 论文翻译成中文
```

### 步骤 3: 等待完成

Claude 会自动：
1. ✅ 检查环境和依赖
2. ✅ 创建翻译脚本
3. ✅ 翻译所有章节文件
4. ✅ 创建中文主文件
5. ✅ 编译生成 PDF

完成后，你会得到：
- `sections_zh/` - 中文章节文件
- `main_zh.tex` - 中文主文件
- `main_zh.pdf` - 最终的中文PDF ✨

## 📋 要求

### 必需
- Python 3.8+
- OpenAI compatible API 配置
- LaTeX 项目（包含 main.tex 和 sections/ 目录）

### 可选（用于PDF编译）
- xelatex
- 中文字体（STSong, STHeiti）

## 💡 示例项目结构

```
my-paper/
├── .env                 ← 第1步：创建这个
├── main.tex             ← 你的英文论文
├── sections/
│   ├── introduction.tex
│   ├── method.tex
│   └── conclusion.tex
└── figures/
    └── ...
```

运行后会生成：

```
my-paper/
├── sections_zh/         ← 新增：翻译后的章节
├── main_zh.tex          ← 新增：中文主文件
└── main_zh.pdf          ← 新增：中文PDF
```

## ⚙️ 高级选项

### 自定义章节目录

如果你的章节不在 `sections/` 目录：

```bash
python translate_latex.py --sections-dir my-sections --output-dir my-sections-zh
```

### 使用不同模型

修改 `.env` 中的 `MODEL_NAME`：

```bash
MODEL_NAME=gpt-4-turbo
# 或
MODEL_NAME=claude-sonnet-4-5
```

### 仅翻译特定文件

编辑 `translate_latex.py` 或直接删除不需要翻译的 .tex 文件。

## 🐛 故障排除

**问题**: 找不到 .tex 文件
**解决**: 确保在正确的目录，或使用 `--sections-dir` 参数

**问题**: API 调用失败
**解决**: 检查 `.env` 中的 API_KEY 和 API_BASE_URL

**问题**: PDF 编译失败
**解决**:
```bash
# 检查 xelatex 是否安装
which xelatex

# 检查中文字体
fc-list :lang=zh-cn
```

**问题**: 翻译质量不理想
**解决**: 尝试使用更强大的模型，或调整提示词

## 🎯 最佳实践

1. **先备份原文件** - 虽然不会修改原文件，但安全第一
2. **分批翻译** - 大型论文可以分多次运行
3. **检查翻译** - 特别注意专业术语和公式
4. **保留格式** - 所有 LaTeX 命令都会被保留
5. **版本控制** - 使用 git 管理翻译过程

## 📞 获取帮助

- 查看完整文档: `~/.claude/skills/translate-latex/README.md`
- 查看提示词: `~/.claude/skills/translate-latex/prompt.md`
- 提交问题: 联系 Claude Code 支持

---

**Happy Translating! 🎉**
