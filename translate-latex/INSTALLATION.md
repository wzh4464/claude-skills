# LaTeX 论文翻译 Skill - 安装指南

## ✅ Skill 已安装

这个 skill 已经安装在：
```
~/.claude/skills/translate-latex/
```

## 📦 文件清单

```
~/.claude/skills/translate-latex/
├── skill.json              # Skill 配置文件
├── prompt.md               # 核心提示词
├── translate_latex.py      # 翻译脚本
├── README.md               # 完整文档
├── QUICKSTART.md           # 快速开始
├── INSTALLATION.md         # 本文件
├── CHANGELOG.md            # 更新日志
└── .env.example            # API 配置模板
```

## 🔧 使用前准备

### 1. Python 依赖

在使用前需要安装 Python 依赖：

```bash
pip install openai python-dotenv
```

或使用虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install openai python-dotenv
```

### 2. API 配置

在你的 LaTeX 项目根目录创建 `.env` 文件：

```bash
# 复制模板
cp ~/.claude/skills/translate-latex/.env.example .env

# 编辑配置
nano .env
```

填入你的 API 配置：

```bash
API_BASE_URL=https://api.chatanywhere.org/v1
API_KEY=sk-your-actual-api-key-here
MODEL_NAME=gpt-4o
```

### 3. LaTeX 环境（可选，用于生成 PDF）

如果要生成 PDF，需要安装 xelatex：

**macOS:**
```bash
brew install --cask mactex
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-xetex texlive-lang-chinese
```

**Windows:**
下载安装 [MiKTeX](https://miktex.org/) 或 [TeX Live](https://www.tug.org/texlive/)

### 4. 中文字体（macOS 通常已有）

检查中文字体：
```bash
fc-list :lang=zh-cn
```

如果没有，安装中文字体：
- macOS: 系统自带 STSong, STHeiti
- Linux: `sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei`
- Windows: 系统自带宋体、黑体

## 🚀 如何使用

### 方法 1: 通过 Slash 命令（推荐）

在 Claude Code 中：

```
/translate-latex
```

### 方法 2: 自然语言

在 Claude Code 中直接说：

```
帮我翻译这个 LaTeX 论文
```

或

```
将这个学术论文翻译成中文并生成 PDF
```

### 方法 3: 直接运行脚本

如果你想手动运行：

```bash
# 复制脚本到项目目录
cp ~/.claude/skills/translate-latex/translate_latex.py .

# 运行翻译
python translate_latex.py --sections-dir sections --output-dir sections_zh
```

## 📋 预期输出

运行后会生成：

```
your-project/
├── sections_zh/           # 新增：翻译后的章节
│   ├── introduction.tex
│   ├── method.tex
│   └── ...
├── main_zh.tex            # 新增：中文主文件
└── main_zh.pdf            # 新增：中文PDF（如果编译成功）
```

## ✨ 功能特性

- ✅ 完整保留 LaTeX 格式
- ✅ 自动识别并跳过已翻译文件
- ✅ 实时显示翻译进度
- ✅ 支持大型论文（分段翻译）
- ✅ 专业术语智能处理
- ✅ 自动添加中文字体支持
- ✅ 一键生成 PDF

## 🔍 验证安装

运行以下命令验证 skill 是否正确安装：

```bash
# 检查 skill 文件
ls -la ~/.claude/skills/translate-latex/

# 检查配置
cat ~/.claude/skills/translate-latex/skill.json

# 测试脚本语法
python3 ~/.claude/skills/translate-latex/translate_latex.py --help
```

## 🐛 常见问题

### Skill 无法识别

1. 确保 skill 目录结构正确
2. 重启 Claude Code
3. 检查 `skill.json` 格式是否正确

### API 调用失败

1. 检查 `.env` 文件是否在正确位置
2. 验证 API_KEY 和 API_BASE_URL
3. 测试 API 连接：

```python
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
client = OpenAI(
    api_key=os.getenv('API_KEY'),
    base_url=os.getenv('API_BASE_URL')
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

### PDF 编译失败

1. 确认安装了 xelatex: `which xelatex`
2. 检查中文字体: `fc-list :lang=zh-cn`
3. 查看编译日志: `cat main_zh.log`

## 📚 更多文档

- 快速开始: `~/.claude/skills/translate-latex/QUICKSTART.md`
- 完整文档: `~/.claude/skills/translate-latex/README.md`
- 提示词: `~/.claude/skills/translate-latex/prompt.md`
- 更新日志: `~/.claude/skills/translate-latex/CHANGELOG.md`

## 💡 使用建议

1. **首次使用**: 先用小型论文测试
2. **大型论文**: 可以分多次运行，利用断点续传
3. **质量检查**: 翻译完成后人工审核专业术语
4. **版本控制**: 使用 git 跟踪翻译版本

## 🎉 开始使用

现在你可以：

```bash
cd /path/to/your/latex/paper
```

然后在 Claude Code 中输入：

```
/translate-latex
```

就这么简单！

---

**需要帮助？** 查看 [QUICKSTART.md](QUICKSTART.md) 获取快速使用指南。
