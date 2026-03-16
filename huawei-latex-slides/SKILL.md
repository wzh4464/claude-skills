---
name: huawei-latex-slides
description: Use when creating LaTeX Beamer presentations in Huawei internal report style, converting Huawei PPT to LaTeX, or building dense technical slides with dark-blue/red color scheme for project proposals (立项报告), technical reports, or competitive analysis decks.
---

# Huawei-Style LaTeX Slides

## Overview

Create high-density LaTeX Beamer presentations that match Huawei's internal report style: dark-blue title bars, #C00000 red emphasis, 微软雅黑/Arial fonts, and extreme information density. Uses `beamerthemeHuawei.sty` template.

## When to Use

- Creating 立项报告, 技术洞察, 竞品分析 slides
- Converting existing Huawei `.pptx` to LaTeX
- Building dense technical presentations with Chinese/English mixed content
- Need the Huawei visual identity (dark blue + dark red + high density)

## Setup

### 1. Copy Template

```bash
cp ~/.claude/skills/huawei-latex-slides/beamerthemeHuawei.sty ./
```

### 2. Document Skeleton

```latex
\documentclass[aspectratio=169, 9pt, xcolor=dvipsnames]{beamer}
\usepackage{beamerthemeHuawei}
\usepackage{pifont}

\title{项目名称}
\subtitle{副标题}
\author{部门名称}
\date{2026}

\begin{document}
\begin{frame}[plain]
  \titlepage
\end{frame}

% Content frames here

\end{document}
```

Compile with: `xelatex main.tex`

## Quick Reference: Available Macros

| Macro | Purpose | Example |
|-------|---------|---------|
| `\hwemph{text}` | Red bold emphasis (#C00000) | `\hwemph{关键结论}` |
| `\hwblue{text}` | Dark blue bold | `\hwblue{标题}` |
| `\hwnote{text}` | Gray footnote text | `\hwnote{来源: xxx}` |
| `\hwgood{text}` | Green positive marker | `\hwgood{领先}` |
| `\hwbad{text}` | Red negative marker | `\hwbad{差距大}` |
| `\hwwarn{text}` | Yellow neutral marker | `\hwwarn{需强化}` |
| `\hwredbar{title}` | Red section header bar | `\hwredbar{洞察 1}` |
| `\hwbluebar{title}` | Blue section header bar | `\hwbluebar{公司现状}` |
| `\hwtocitem{num}{title}` | TOC navigation block | `\hwtocitem{1}{项目环境}` |
| `\hwtablestyle` | Apply table styling | Before `tabularx` |

| Environment | Purpose |
|-------------|---------|
| `hwbox[title]` | Light-blue info box |
| `hwdarkbox[title]` | Dark-blue info box (white text) |

## Color Palette

| Name | HEX | Role |
|------|-----|------|
| `hwTextMain` | #1D1D1A | Body text (warm dark gray, NOT pure black) |
| `hwRed` | #C00000 | **Primary accent** — keywords, conclusions, emphasis |
| `hwDarkBlue` | #1B2A4A | Title bar background, section headers |
| `hwLightBlue` | #E8EEF9 | Info box fill, table alternating rows |
| `hwGreen` | #00B050 | Positive / good status |
| `hwRedBright` | #FF0000 | Negative / gap marker |
| `hwYellow` | #FFC000 | Warning / neutral status |
| `hwGray` | #666666 | Secondary text, footnotes |

## Slide Patterns

### Pattern 1: Two-Column Analysis (most common)

```latex
\begin{frame}{标题：问句或判断句式}
  \vspace{-2mm}
  {\footnotesize 一句话摘要，含\hwemph{关键词高亮}。}
  \vspace{1.5mm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \hwbluebar{左栏标题}
      {\footnotesize
      \begin{itemize}
        \item 要点一
        \item \hwemph{强调要点}
      \end{itemize}
      }
      \vspace{1mm}
      \hwredbar{洞察}
      {\footnotesize 洞察内容... }
    \end{column}
    \begin{column}{0.48\textwidth}
      \hwbluebar{右栏标题}
      {\footnotesize ... }
      \vspace{1mm}
      \begin{hwbox}[核心结论]
        结论内容，含\hwemph{关键词}。
      \end{hwbox}
    \end{column}
  \end{columns}
\end{frame}
```

### Pattern 2: Comparison Table

```latex
\begin{frame}{对比标题}
  \vspace{-2mm}
  {\scriptsize
  \hwtablestyle
  \begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{18mm}
    >{\raggedright\arraybackslash}X
    >{\raggedright\arraybackslash}X
    >{\raggedright\arraybackslash}p{25mm}}
    \toprule
    \rowcolor{hwDarkBlue}
    \textcolor{hwWhite}{\textbf{维度}} &
    \textcolor{hwWhite}{\textbf{标杆}} &
    \textcolor{hwWhite}{\textbf{现状}} &
    \textcolor{hwWhite}{\textbf{差距}} \\
    \midrule
    能力A & \hwgood{领先} & 基本 & \hwbad{差距大} \\
    能力B & 中等 & 中等 & \hwwarn{需强化} \\
    \bottomrule
  \end{tabularx}
  }
\end{frame}
```

### Pattern 3: Architecture Diagram (TikZ)

```latex
\begin{frame}{架构标题}
  \vspace{-2mm}
  \begin{tikzpicture}[
    module/.style={draw=hwDarkBlue, fill=hwLightBlue, rounded corners=2pt,
      minimum width=22mm, minimum height=10mm, align=center,
      font=\tiny\bfseries, text width=20mm},
    core/.style={draw=hwDarkBlue, fill=hwDarkBlue, text=hwWhite,
      rounded corners=3pt, minimum width=30mm, minimum height=12mm,
      align=center, font=\small\bfseries},
    arr/.style={-{Stealth[length=2mm]}, hwGray, thick},
    redarr/.style={-{Stealth[length=2mm]}, hwRed, thick},
  ]
    \node[core] (center) at (6,0) {核心模块};
    \node[module] (m1) at (2,1.5) {子模块 1};
    \node[module] (m2) at (10,1.5) {子模块 2};
    \draw[arr] (m1) -- (center);
    \draw[redarr] (center) -- (m2);
  \end{tikzpicture}
\end{frame}
```

### Pattern 4: Timeline / Phase Diagram

```latex
\begin{tikzpicture}[
  phase/.style={draw=hwDarkBlue, fill=hwLightBlue, rounded corners=3pt,
    minimum width=26mm, minimum height=16mm, align=center,
    font=\footnotesize, text width=25mm},
  arrow/.style={-{Stealth[length=3mm]}, thick, hwRed},
]
  \node[phase] (p1) at (0,0) {\textbf{Phase 1}\\描述\\{\tiny 时间}};
  \node[phase] (p2) at (3.5,0) {\textbf{Phase 2}\\描述};
  \node[phase, fill=hwRed!15, draw=hwRed] (p3) at (7,0) {
    \textbf{Phase 3}\\\textcolor{hwRed}{当前}};
  \draw[arrow] (p1) -- (p2);
  \draw[arrow] (p2) -- (p3);
\end{tikzpicture}
```

### Pattern 5: Flow / Process Chain

```latex
\begin{tikzpicture}[
  box/.style={draw=hwDarkBlue, fill=hwLightBlue, rounded corners=2pt,
    minimum width=14mm, minimum height=9mm, align=center,
    font=\tiny\bfseries},
  arr/.style={-{Stealth[length=2mm]}, hwDarkBlue, thick},
]
  \node[box] (s1) at (0,0) {步骤1};
  \node[box] (s2) at (2,0) {步骤2};
  \node[box] (s3) at (4,0) {步骤3};
  \foreach \i/\j in {s1/s2, s2/s3}
    \draw[arr] (\i) -- (\j);
\end{tikzpicture}
```

## Style Rules (from PPT analysis)

1. **Information density**: Fill every slide. No whitespace at bottom. Use `\vspace{-2mm}` after frame title, `\vspace{1mm}` between sections.
2. **Font sizes**: Body `\footnotesize`, tables `\scriptsize`, notes `\scriptsize`. Documentclass `9pt`.
3. **Title style**: Use questions ("为什么...?") or judgment statements with colon ("核心洞察：xxx").
4. **Red emphasis**: Use `\hwemph{}` liberally for keywords, numbers, conclusions. #C00000 is the soul of the style.
5. **Section bars**: Use `\hwredbar{}` for key insights/conclusions, `\hwbluebar{}` for categories/sections.
6. **Traffic lights**: `\hwgood{}` / `\hwbad{}` / `\hwwarn{}` in comparison tables.
7. **No `enumitem`**: Conflicts with Beamer. Use native list environments without options.
8. **Chinese-English mix**: Keep technical terms in English (Agent, Scaffold, Context Engineering).
9. **Line spread**: Already set to 0.9 in theme. Don't override.
10. **Margins**: 6mm left/right. Tight but readable.

## Converting from PPTX

When converting an existing Huawei `.pptx`:

1. **Extract text**: Unzip PPTX, parse slide XML for `<a:t>` tags
2. **Identify page type**: Architecture diagram → Pattern 3; Comparison → Pattern 2; Analysis → Pattern 1
3. **Map colors**: Check if the PPTX uses custom colors beyond the standard palette
4. **Reproduce iteratively**: Build one slide at a time, compile, compare visually with original
5. **Fill space**: If bottom of slide is empty, add more content — original PPTs have extreme density

```bash
# Extract text from PPTX
mkdir -p /tmp/pptx_out && unzip -o "file.pptx" -d /tmp/pptx_out
for f in /tmp/pptx_out/ppt/slides/slide*.xml; do
  echo "=== $(basename $f) ==="
  cat "$f" | sed 's/</\n</g' | grep 'a:t>' | sed 's/.*<a:t>//; s/<\/a:t.*//'
done
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `enumitem` package | Remove it — conflicts with Beamer, causes infinite loop |
| Pure black text (#000000) | Use #1D1D1A (warm dark gray) |
| Too much whitespace | Reduce `\vspace`, add content, use `9pt` documentclass |
| Large font sizes | Body should be `\footnotesize`, not `\small` or `\normalsize` |
| Missing `colortbl` | Required for `\rowcolors` in tables |
| TikZ elements overflow | Keep x-coordinates within 0-12 range for 16:9 slides |
| `\\` in last line before `\end{frame}` | Causes overfull hbox — use paragraph break instead |
