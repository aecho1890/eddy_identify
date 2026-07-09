# Baseline comparison tool

`scripts/compare_eddy_baseline.py` 用于比较两个 baseline 统计结果。它是只读工具，不运行涡旋识别，也不修改任何算法文件。

通常工作流为：

```text
旧版本 JSON
  ↓ summarize_eddy_json.py
baseline_summary.csv / baseline_records.csv

新版本 JSON
  ↓ summarize_eddy_json.py
new_summary.csv / new_records.csv

baseline_summary.csv + new_summary.csv
baseline_records.csv + new_records.csv
  ↓ compare_eddy_baseline.py
comparison report
```

## 1. 比较 summary

用于快速判断总体结果有没有变化。

```bash
python scripts/compare_eddy_baseline.py summary \
  baseline_summary.csv \
  new_summary.csv \
  --out-csv summary_compare.csv
```

重点查看：

| 字段 | 含义 |
|---|---|
| `detected_eddies` | 总涡旋数量是否一致 |
| `anticyclonic_eddies` | 反气旋数量是否一致 |
| `cyclonic_eddies` | 气旋数量是否一致 |
| `mean_radius` | 平均半径是否变化 |
| `mean_amplitude` | 平均振幅是否变化 |
| `mean_Uavg_max` | 最大平均速度边界速度是否变化 |
| `mean_EKE` | EKE 是否变化 |

如果只是文档修改或路径整理，理论上这些值应该完全一致。

## 2. 比较 records

用于逐个涡旋检查新增、删除和匹配情况。

```bash
python scripts/compare_eddy_baseline.py records \
  baseline_records.csv \
  new_records.csv \
  --match-distance-deg 0.25 \
  --out-csv records_compare.csv
```

输出中的 `status` 包括：

| status | 含义 |
|---|---|
| `matched` | baseline 和 new 中找到可匹配涡旋 |
| `missing_in_new` | baseline 中有，但 new 中没有 |
| `new_only` | new 中新增，baseline 中没有 |

匹配规则：

1. 默认按同极性涡旋进行最近邻匹配；
2. 涡心距离小于等于 `--match-distance-deg` 才认为匹配；
3. 经度会近似考虑 0/360° 周期边界；
4. 如果增加 `--name-match-first`，会优先匹配同名涡旋。

## 3. 推荐阈值

对于 0.25° 数据，建议：

```bash
--match-distance-deg 0.25
```

如果只是轻微路径重构或 I/O 重构，这个阈值足够严格。

如果后续改了滤波、shape error、振幅阈值等算法参数，可以临时放宽到：

```bash
--match-distance-deg 0.5
```

但这种情况必须额外解释为什么结果发生变化。

## 4. 建议判断标准

### 4.1 文档或环境修改

必须满足：

```text
detected_eddies difference = 0
anticyclonic_eddies difference = 0
cyclonic_eddies difference = 0
missing_in_new = 0
new_only = 0
```

### 4.2 路径配置化

原则上也必须满足完全一致。

如果不一致，优先检查：

- 输入文件是否相同；
- 变量名是否相同；
- lon/lat 是否发生半格点偏移；
- mask 是否发生变化；
- 单位是否发生变化。

### 4.3 I/O 层重构

必须重点检查：

- `core_lon` / `core_lat` 是否整体偏移；
- SLA 是否单位改变，例如 m 与 cm 混用；
- u/v 是否单位改变，例如 m/s 与 cm/s 混用；
- 缺测值 mask 是否一致。

### 4.4 算法优化

允许结果变化，但必须报告：

- 新增涡旋案例；
- 删除涡旋案例；
- 半径变化明显案例；
- 振幅变化明显案例；
- 对比图。

## 5. 完整示例

```bash
# 1. 统计旧版本结果
python scripts/summarize_eddy_json.py \
  baseline/eddy_info_merge20250101.json \
  --records-csv baseline_records.csv \
  --summary-csv baseline_summary.csv

# 2. 统计新版本结果
python scripts/summarize_eddy_json.py \
  new/eddy_info_merge20250101.json \
  --records-csv new_records.csv \
  --summary-csv new_summary.csv

# 3. 比较总体指标
python scripts/compare_eddy_baseline.py summary \
  baseline_summary.csv \
  new_summary.csv \
  --out-csv summary_compare.csv

# 4. 比较逐涡旋记录
python scripts/compare_eddy_baseline.py records \
  baseline_records.csv \
  new_records.csv \
  --match-distance-deg 0.25 \
  --out-csv records_compare.csv
```

## 6. 当前阶段作用

该工具用于后续重构的质量控制。它本身不参与识别流程，只用于回答：

> 这次修改有没有改变涡旋识别结果？如果改变了，具体改变在哪里？
