# PPT 模板目录

将北信科官方 PPT 模板放入此目录。

## 可用模板

| 模板文件 | 说明 | 适用场景 |
|----------|------|----------|
| `PPT-浅蓝色.pptx` | 浅蓝色主题模板 | 通用汇报、课程展示 |

## 使用方式

```bash
# 查看可用模板
python3 scripts/generate_ppt.py --list-templates

# 使用模板生成 PPT
python3 scripts/generate_ppt.py \
  --title "我的答辩" \
  --markdown content.md \
  --template "PPT-浅蓝色.pptx" \
  --output output.pptx
```

## 模板制作指南

1. 使用北信科官方配色：
   - 主题蓝: `#00468C` (RGB: 0, 70, 140)
   - 辅助灰: `#808080`
   - 背景白: `#FFFFFF`

2. 包含以下版式：
   - 封面页
   - 目录页
   - 内容页（标题+正文）
   - 图片页
   - 结束页

3. 每个版式命名清晰，便于 python-pptx 识别

## 获取更多模板

- 联系学校宣传部或教务处获取官方模板
- 或自行制作符合学校视觉规范的模板
