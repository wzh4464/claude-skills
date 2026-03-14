# LaTeX 论文翻译 Skill

这个 skill 可以将英文 LaTeX 学术论文自动翻译成中文，并生成保留原始格式的 PDF 文件。

## 功能特点

- ✅ 使用 OpenAI compatible API 进行翻译
- ✅ 完整保留 LaTeX 格式、命令、引用
- ✅ 自动添加中文字体支持
- ✅ 支持断点续传（跳过已翻译文件）
- ✅ 实时显示翻译进度
- ✅ 自动编译生成中文 PDF

## 使用方法

### 前置条件

1. **环境变量配置**：在项目根目录创建 `.env` 文件：
   ```bash
   API_BASE_URL=https://api.chatanywhere.org/v1
   API_KEY=your-api-key-here
   MODEL_NAME=gpt-4o
   ```

2. **系统要求**：
   - Python 3.8+
   - xelatex（用于编译中文PDF）
   - 中文字体（STSong, STHeiti 等）

### 调用方式

在 Claude Code 中，只需说：

```
/translate-latex
```

或者：

```
帮我翻译这个 LaTeX 论文
```

### 工作流程

1. **环境检查** - 验证 API 配置和 LaTeX 环境
2. **创建脚本** - 生成翻译脚本
3. **翻译章节** - 逐个翻译 sections/ 目录下的 .tex 文件
4. **创建主文件** - 生成包含中文支持的 main_zh.tex
5. **编译PDF** - 使用 xelatex 编译生成 main_zh.pdf

## 目录结构

```
project/
├── .env                    # API 配置
├── main.tex               # 原始英文主文件
├── main_zh.tex            # 生成的中文主文件
├── main_zh.pdf            # 最终的中文PDF
├── sections/              # 原始英文章节
│   ├── introduction.tex
│   ├── method.tex
│   └── ...
└── sections_zh/           # 翻译后的中文章节
    ├── introduction.tex
    ├── method.tex
    └── ...
```

## 翻译质量保证

- **术语一致性**：专业术语首次出现时附带英文注释
- **格式完整性**：所有 LaTeX 命令、引用、标签原样保留
- **段落结构**：保持原文的段落划分和层次
- **学术规范**：遵循学术论文的翻译规范

## 配置选项

可以通过命令行参数自定义：

```bash
python translate_latex.py --sections-dir sections --output-dir sections_zh --model gpt-4o
```

## 常见问题

**Q: 翻译中断了怎么办？**
A: 再次运行即可，脚本会自动跳过已翻译的文件。

**Q: 如何修改翻译质量？**
A: 可以修改 `.env` 中的 MODEL_NAME 使用不同的模型。

**Q: PDF 编译失败？**
A: 检查是否安装了 xelatex 和中文字体。

**Q: 支持哪些语言方向？**
A: 当前支持英文→中文，可以修改提示词支持其他语言。

## 版本历史

- **1.0.0** (2025-02-04)
  - 初始版本
  - 支持基本的英文→中文翻译
  - 自动PDF生成

## 作者

Claude AI Assistant

## 许可

MIT License
