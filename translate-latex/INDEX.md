# LaTeX 论文翻译 Skill - 文件索引

## 📁 目录结构

```
~/.claude/skills/translate-latex/
├── skill.json              # Skill 元数据配置
├── prompt.md               # 核心提示词 (6.2KB, 200+ 行)
├── translate_latex.py      # 翻译脚本 (4.3KB, 120+ 行)
├── README.md               # 完整文档 (2.7KB)
├── QUICKSTART.md           # 快速开始指南 (2.9KB)
├── INSTALLATION.md         # 详细安装说明 (4.7KB)
├── CHANGELOG.md            # 版本更新日志 (1.3KB)
├── .env.example            # API 配置模板
└── INDEX.md                # 本文件 - 文件索引
```

**总计**: 889 行代码和文档

## 📄 文件说明

### 核心文件

#### skill.json
- **用途**: Skill 配置文件
- **内容**: 名称、版本、描述、参数定义
- **大小**: 374B
- **格式**: JSON

#### prompt.md
- **用途**: 核心提示词，定义 Skill 行为
- **内容**: 工作流程、翻译策略、注意事项
- **大小**: 6.2KB
- **行数**: 200+
- **关键章节**:
  - 环境检查
  - 创建翻译脚本
  - 翻译章节文件
  - 创建中文主文件
  - 编译PDF
  - 验证结果

#### translate_latex.py
- **用途**: 实际执行翻译的 Python 脚本
- **大小**: 4.3KB
- **行数**: 120+
- **主要函数**:
  - `translate_chunk()`: 翻译单个文本块
  - `translate_file()`: 翻译单个文件
  - `main()`: 主函数，处理命令行参数
- **依赖**: openai, python-dotenv

### 文档文件

#### README.md
- **用途**: 完整的功能说明和使用文档
- **大小**: 2.7KB
- **内容**:
  - 功能特点
  - 使用方法
  - 目录结构
  - 翻译质量保证
  - 常见问题

#### QUICKSTART.md
- **用途**: 5分钟快速开始指南
- **大小**: 2.9KB
- **内容**:
  - 3步快速使用
  - 示例项目结构
  - 高级选项
  - 故障排除
  - 最佳实践

#### INSTALLATION.md
- **用途**: 详细的安装和配置指南
- **大小**: 4.7KB
- **内容**:
  - 安装验证
  - Python 依赖配置
  - API 配置
  - LaTeX 环境
  - 中文字体
  - 常见问题

#### CHANGELOG.md
- **用途**: 版本更新历史
- **大小**: 1.3KB
- **内容**:
  - 1.0.0 版本功能
  - 未来计划
  - 待改进项目

### 配置文件

#### .env.example
- **用途**: API 配置模板
- **大小**: 448B
- **包含**:
  - API_BASE_URL
  - API_KEY
  - MODEL_NAME
  - 备用配置选项

## 🔍 快速导航

### 我想...

| 目标 | 查看文件 |
|------|----------|
| 快速上手使用 | [QUICKSTART.md](QUICKSTART.md) |
| 了解完整功能 | [README.md](README.md) |
| 安装和配置 | [INSTALLATION.md](INSTALLATION.md) |
| 查看更新历史 | [CHANGELOG.md](CHANGELOG.md) |
| 了解工作原理 | [prompt.md](prompt.md) |
| 查看翻译脚本 | [translate_latex.py](translate_latex.py) |
| 配置 API | [.env.example](.env.example) |

## 📊 统计信息

- **总文件数**: 9 个文件
- **总代码量**: 889 行
- **脚本大小**: 4.3KB
- **文档大小**: 18.8KB
- **语言**: Python, Markdown, JSON
- **版本**: 1.0.0
- **创建日期**: 2025-02-04

## 🎯 核心功能

1. **自动翻译**: 使用 OpenAI API 翻译 LaTeX 论文
2. **格式保留**: 100% 保留 LaTeX 命令和结构
3. **进度显示**: 实时显示翻译进度
4. **断点续传**: 自动跳过已翻译文件
5. **PDF 生成**: 自动编译中文 PDF
6. **质量保证**: 专业术语智能标注

## 🚀 使用流程

```
用户调用 (/translate-latex)
    ↓
prompt.md (提示词指导)
    ↓
创建并运行 translate_latex.py
    ↓
翻译所有章节文件 (sections/ → sections_zh/)
    ↓
创建中文主文件 (main_zh.tex)
    ↓
编译 PDF (main_zh.pdf)
    ↓
完成！
```

## 📞 获取帮助

- **快速问题**: 查看 [QUICKSTART.md](QUICKSTART.md)
- **安装问题**: 查看 [INSTALLATION.md](INSTALLATION.md)
- **功能问题**: 查看 [README.md](README.md)
- **深入了解**: 查看 [prompt.md](prompt.md)

## 🔄 更新方式

检查新版本：
```bash
cat ~/.claude/skills/translate-latex/CHANGELOG.md
```

更新 skill：
```bash
# 备份当前版本
cp -r ~/.claude/skills/translate-latex ~/.claude/skills/translate-latex.backup

# 下载新版本（待实现）
# git clone ... ~/.claude/skills/translate-latex
```

## 📝 贡献

如果你有改进建议：

1. 编辑对应的文件
2. 更新 CHANGELOG.md
3. 增加版本号（如果需要）
4. 测试新功能

## 🎓 了解更多

- [LaTeX 官方文档](https://www.latex-project.org/)
- [xeCJK 文档](https://ctan.org/pkg/xecjk)
- [OpenAI API 文档](https://platform.openai.com/docs)

---

**最后更新**: 2025-02-04
**版本**: 1.0.0
**维护者**: Claude AI Assistant
