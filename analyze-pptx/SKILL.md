---
name: analyze-pptx
description: Use when analyzing a .pptx file's format, colors, fonts, layout, or design preferences. Trigger on requests like "analyze this PPT", "what colors does this slide use", "extract the style from this presentation".
---

# Analyze PPTX Format & Style

## Overview

Extract format, colors, fonts, sizes, shapes, and layout from `.pptx` files by unzipping and parsing the internal XML structure. No external dependencies needed.

## When to Use

- User wants to understand a PPT's visual style/design preferences
- Need to replicate a PPT's color scheme or format in another context (e.g., HTML slides, LaTeX)
- Comparing design styles across presentations
- Extracting a "style profile" before creating new slides matching an existing deck

## Core Technique

`.pptx` is a ZIP archive containing XML files. Unzip and parse the XML to extract all styling data.

### Step 1: Unzip

```bash
mkdir -p /tmp/pptx_extracted
unzip -o "file.pptx" -d /tmp/pptx_extracted
```

### Step 2: Identify Structure

Key files:
```
ppt/slides/slide{N}.xml          # Slide content, shapes, inline styles
ppt/slides/_rels/slide{N}.xml.rels  # Image/layout references per slide
ppt/slideLayouts/slideLayout{N}.xml # Layout templates
ppt/slideMasters/slideMaster{N}.xml # Master slide definitions
ppt/theme/theme{N}.xml           # Theme color palette & font scheme
ppt/media/                       # Embedded images
ppt/presentation.xml             # Slide dimensions, slide order
```

To find which theme a slide uses, follow the chain:
```
slide → _rels → slideLayout → _rels → slideMaster → _rels → theme
```

### Step 3: Extract Colors

The XML is often single-line. Use `sed` to split before grepping:

```bash
# Explicit RGB colors (most important - these are custom overrides)
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -o 'srgbClr val="[0-9A-Fa-f]*"' | sort | uniq -c | sort -rn

# Theme color references (mapped to theme palette)
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -o 'schemeClr val="[a-zA-Z0-9]*"' | sort | uniq -c | sort -rn
```

### Step 4: Extract Theme Color Palette

```bash
# Get full color scheme from theme file
cat ppt/theme/theme{N}.xml | sed 's/>/>\n/g' | \
  sed -n '/a:clrScheme/,/\/a:clrScheme/p'
```

Theme color mapping:
| XML Name | Role |
|----------|------|
| `dk1` | Dark text 1 (usually black) |
| `lt1` | Light background 1 (usually white) |
| `dk2` | Dark text 2 |
| `lt2` | Light background 2 |
| `accent1`-`accent6` | Accent colors |
| `hlink` | Hyperlink color |
| `folHlink` | Followed hyperlink |

### Step 5: Extract Fonts

```bash
# Latin (Western) fonts
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -o 'latin typeface="[^"]*"' | sort | uniq -c | sort -rn

# East Asian fonts (Chinese/Japanese/Korean)
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -o 'ea typeface="[^"]*"' | sort | uniq -c | sort -rn
```

Font reference values:
- `+mj-lt` / `+mj-ea` = Major (heading) font from theme
- `+mn-lt` / `+mn-ea` = Minor (body) font from theme
- Explicit name (e.g., `微软雅黑`) = Custom override

### Step 6: Extract Font Sizes

```bash
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -o 'sz="[0-9]*"' | sort | uniq -c | sort -rn
```

Size values are in **hundredths of a point**: `1200` = 12pt, `3200` = 32pt.

### Step 7: Extract Shapes & Layout

```bash
# Shape types
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -E 'prstGeom|custGeom' | grep -o 'prst="[^"]*"' | sort | uniq -c | sort -rn

# Count total shapes
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | grep -c '<p:sp'

# Count images
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | grep -c 'blipFill'

# Line widths (in EMUs: 12700 = 1pt)
cat ppt/slides/slide1.xml | sed 's/>/>\n/g' | \
  grep -o 'ln w="[0-9]*"' | sort | uniq -c | sort -rn
```

### Step 8: Extract Text Content

```bash
cat ppt/slides/slide1.xml | sed 's/</\n</g' | \
  grep 'a:t>' | sed 's/.*<a:t>//; s/<\/a:t.*//'
```

## Output Format

Present analysis as a structured report:

1. **Color Palette** - Table with HEX, swatch description, usage frequency, inferred role
2. **Theme Colors** - Mapped accent/text/background colors
3. **Fonts** - Primary fonts for Latin and CJK, with frequency
4. **Font Sizes** - Distribution indicating content density style
5. **Layout** - Shape count, types, images, structural pattern
6. **Style Summary** - Table summarizing overall design personality (dense vs. sparse, formal vs. casual, color mood)

## Common Pitfalls

- **macOS `grep` lacks `-P` flag** — use `sed 's/>/>\n/g'` to split XML then pipe to basic `grep -o`
- **Single-line XML** — always split before grepping; raw XML is typically one giant line
- **Theme indirection** — slide colors referencing `schemeClr` need theme file lookup to get actual HEX
- **Multiple themes** — large decks may have many theme files; follow the rels chain per slide
- **EMU units** — positions/sizes in XML are in EMUs (914400 EMU = 1 inch)
