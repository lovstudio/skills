---
title: Test Plan Verification
subtitle: md2pdf Bug Fixes & New Features
author: Test Runner
date: 2026-04-12
---

# 第一部分：Bug Fixes

## 第1章 Code Span with Asterisks

This tests that inline code containing `*` does not conflict with italic regex.

- Code span with single star: `foo*bar`
- Code span with double star: `foo**bar**baz`
- Code span with multiple stars: `a*b*c*d`
- Normal italic for comparison: *this is italic*
- Normal bold for comparison: **this is bold**
- Mixed: `code*star` then *italic* then `more*code`

## 第2章 Tables with Hash Signs

This tests that table rows containing # are not split as headings.

| Feature | Count | Notes |
|---------|-------|-------|
| Item #1 | 10 | First item with # |
| C# code | 20 | Language name with # |
| Issue #42 | 5 | Reference with # sign |

Another paragraph after the table.

### 2.1 Sub-section after table

Content after a sub-section following a table.

## 第3章 HTML Anchor Tags

<a name="section-anchor"></a>

This paragraph should appear after the anchor tag is skipped.

<a id="another-anchor"></a>

More content after another anchor.

## 第4章 H3+ Headings

### Three hashes heading

Content under H3.

#### Four hashes heading

Content under H4.

##### Five hashes heading

Content under H5.

# 第二部分：New Features

## 第5章 Heading Spacer Test

This chapter tests configurable heading top spacer.
The spacer before this heading should be adjustable.

### 5.1 Regular sub-section

Normal content under a sub-section.

## 第6章 Watermark Test

This chapter tests watermark customization parameters.
The watermark should appear with custom size, opacity, angle, and spacing.

中文水印测试内容。这里有一些中英文混排的文本，用来验证水印在中文内容上的显示效果。

```python
# This is a code block
def hello():
    print("Hello, World!")
```

End of test document.
