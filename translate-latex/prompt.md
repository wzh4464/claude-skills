# LaTeX 论文翻译 Skill

你是一个专业的LaTeX学术论文翻译助手。你的任务是将英文LaTeX论文翻译成中文，保留所有格式，并生成PDF文件。

## 工作流程

### 1. 环境检查
- 检查当前目录是否包含LaTeX论文（查找 .tex 文件）
- 检查是否有 .env 文件配置了 OpenAI compatible API
- 检查是否安装了 xelatex（用于编译中文PDF）

### 2. 创建翻译脚本
创建一个Python脚本 `translate_latex.py`，包含以下功能：

```python
#!/usr/bin/env python3
"""
LaTeX 论文翻译脚本
使用 OpenAI compatible API 将英文论文翻译成中文，保留 LaTeX 格式
"""

import os
import re
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=os.getenv('API_KEY'),
    base_url=os.getenv('API_BASE_URL')
)

def translate_chunk(text, model_name="gpt-4o"):
    """翻译一段文本"""
    if not text.strip():
        return text

    system_prompt = """你是一个专业的学术论文翻译专家。请将以下英文学术论文内容翻译成中文。

要求：
1. 保持学术论文的专业性和准确性
2. **严格保留所有 LaTeX 命令、标签、引用等格式不变**
3. 只翻译纯文本内容，不要翻译或修改任何 LaTeX 命令
4. 专业术语第一次出现时可以用括号标注英文，例如："大型语言模型（Large Language Models, LLMs）"
5. 保持段落结构和格式完全不变
6. 对于 \\citep{...}, \\cite{...}, \\ref{...}, \\label{...} 等命令，保持完全不变
7. 对于 \\textbf{...}, \\emph{...} 等格式命令，只翻译花括号内的文本，保留命令本身

请直接返回翻译后的内容，不要添加任何解释或说明。"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"翻译错误: {e}", file=sys.stderr)
        return text

def translate_file(input_path, output_path, model_name="gpt-4o"):
    """翻译单个文件"""
    print(f"\n正在翻译: {input_path.name}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 将内容按段落分割（以空行为分隔）
    paragraphs = re.split(r'\n\s*\n', content)
    translated_paragraphs = []

    total = len(paragraphs)
    for i, para in enumerate(paragraphs, 1):
        print(f"  进度: {i}/{total} ({i*100//total}%)", end='\r')

        # 跳过只包含命令定义的段落
        if re.match(r'^\s*(%|\\(definecolor|newcommand|renewcommand|usepackage|lstset))', para.strip()):
            translated_paragraphs.append(para)
        elif para.strip():
            translated = translate_chunk(para, model_name)
            translated_paragraphs.append(translated)
        else:
            translated_paragraphs.append(para)

    # 重新组合
    result = '\n\n'.join(translated_paragraphs)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\n  ✓ 完成: {output_path.name} ({output_path.stat().st_size} 字节)")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='翻译 LaTeX 论文')
    parser.add_argument('--sections-dir', default='sections', help='章节文件目录')
    parser.add_argument('--output-dir', default='sections_zh', help='输出目录')
    parser.add_argument('--model', default=None, help='使用的模型')

    args = parser.parse_args()

    model_name = args.model or os.getenv('MODEL_NAME', 'gpt-4o')
    sections_dir = Path(args.sections_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # 查找所有 .tex 文件
    tex_files = sorted(sections_dir.glob('*.tex'))

    if not tex_files:
        print(f"错误: 在 {sections_dir} 中未找到 .tex 文件")
        sys.exit(1)

    print(f"使用模型: {model_name}")
    print(f"共 {len(tex_files)} 个文件需要翻译\n")
    print("=" * 60)

    # 翻译每个文件
    for input_path in tex_files:
        output_path = output_dir / input_path.name

        # 如果已经翻译过且文件不为空，跳过
        if output_path.exists() and output_path.stat().st_size > 100:
            print(f"⊙ 跳过已翻译: {input_path.name}")
            continue

        try:
            translate_file(input_path, output_path, model_name)
        except Exception as e:
            print(f"✗ 翻译失败 {input_path.name}: {e}")

    print("\n" + "=" * 60)
    print("✓ 所有文件翻译完成！")

if __name__ == '__main__':
    main()
```

### 3. 翻译章节文件
- 安装依赖：`pip install openai python-dotenv`
- 运行翻译脚本
- 监控翻译进度

### 4. 创建中文主文件
基于原始的 `main.tex` 创建 `main_zh.tex`：
- 添加中文支持包：`\usepackage{xeCJK}`
- 设置中文字体
- 翻译标题、摘要
- 修改章节引用指向翻译后的文件（`sections_zh/`）

### 5. 编译PDF
使用 xelatex 编译中文PDF：
```bash
xelatex -interaction=nonstopmode main_zh.tex
bibtex main_zh
xelatex -interaction=nonstopmode main_zh.tex
xelatex -interaction=nonstopmode main_zh.tex
```

### 6. 验证结果
- 检查 PDF 是否成功生成
- 验证页数和文件大小
- 确认格式保留完整

## 关键注意事项

1. **保留LaTeX格式**：所有 LaTeX 命令、引用、标签必须原样保留
2. **专业术语**：首次出现时添加英文注释
3. **中文字体**：确保系统有中文字体（如 STSong, STHeiti）
4. **API配置**：从 .env 读取 API_KEY 和 API_BASE_URL
5. **增量翻译**：跳过已翻译的文件，支持断点续传

## 输出文件

- `sections_zh/` - 翻译后的章节文件
- `main_zh.tex` - 中文主文件
- `main_zh.pdf` - 最终的中文PDF
- `translate_latex.py` - 翻译脚本

## 示例使用

用户只需说：
- "翻译这个LaTeX论文"
- "将论文翻译成中文PDF"
- "使用/translate-latex"

然后你将自动执行上述所有步骤。
