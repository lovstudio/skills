# Surface Audit Workflow

这是 `lov-human-writing` 的内部确定性阶段，不判断作者身份。

## 步骤

1. 从场景推断 `wechat`、`zhuque`、`neutral` 或 `thesis` 档位。
2. 运行根目录 `scripts/measure.py`，读取压力分、越界项和靶点句。
3. 把结果表述为真人分布定位，不表述为 AI 作者判定。
4. 改写后使用 `--compare`；目标指标改善且没有把其他指标推出界才通过。
5. 指标与作者真实风格冲突时，保留作者选择并说明原因。
