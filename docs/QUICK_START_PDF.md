# Markdown转PDF - 快速使用

## 一键转换

```bash
# 1. 激活环境
source /home/Research_work/24_yzlin/LCA-LLM/lcaLLM/bin/activate

# 2. 转换单个文档
python scripts/md_to_pdf.py dataset/documents/your_document.md

# 3. 批量转换所有文档
for file in dataset/documents/phase9/*.md; do python scripts/md_to_pdf.py "$file"; done
```

## 样式效果

✅ **工程报告风格**
- Times New Roman衬线字体
- 标题居中带下划线
- 表格灰色表头、细边框、斑马纹
- A4页面，专业排版

## 自定义

编辑 `md2pdf_fixed.css` 修改样式

## 文件

- `md2pdf_fixed.css` - 样式文件
- `scripts/md_to_pdf.py` - 转换脚本
- `README_MD_TO_PDF.md` - 详细文档
