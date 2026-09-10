# Changelog

## 0.1.0

- 初始版本：1080 宽手机信息图，支持 `3:4`、`4:5`、`9:16`、`1:1` 与 `long` 五种画布比例。
- 六个语义模板：`single-claim`、`step-strip`、`metric-focus`、`compare-pair`、`checklist-gate`、`quote-evidence`。
- `scripts/infographic_cli.py`：`init-brand`、`scaffold`、`render`、`audit` 四个子命令。
- 移动可读性门禁：字号下限、行宽上限、对比度、安全区、裁切与越界、单一结论、证据挂载、
  品牌页脚、系列页码、骨架文案残留与省略号截断，100 分制代理分与 85 分阈值。
- 真实案例：三卡系列，机器审计 3/3 通过（各 100/100），附原图与 320px 缩略图复核记录。
