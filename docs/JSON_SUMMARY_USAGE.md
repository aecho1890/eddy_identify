# JSON summary tool

`scripts/summarize_eddy_json.py` 是一个只读工具，用于读取已有涡旋识别 JSON 结果并生成 baseline 统计表。它不调用任何识别函数，也不修改算法输出。

## 1. 适用输入

支持以下常见旧格式。

### 1.1 `reject()` 后的扁平结果

```json
{
  "eddy_118.625_19.125": {
    "sign_type": "Anticyclonic",
    "eddy_core": [118.625, 19.125, 12.5]
  },
  "seed_120.125_20.375": {
    "sign_type": "Cyclonic",
    "eddy_core": [120.125, 20.375, -5.2]
  }
}
```

### 1.2 合并前的嵌套结果

```json
{
  "inner": {
    "Block_0_0": {
      "eddy_118.625_19.125": {
        "sign_type": "Anticyclonic"
      }
    }
  },
  "outer": {
    "Block_0_1": {
      "eddy_121.125_21.875": {
        "sign_type": "Cyclonic"
      }
    }
  }
}
```

### 1.3 旧版 list-wrapped JSON

如果 JSON 最外层是 list，脚本会递归展开。

## 2. 基本用法

```bash
python scripts/summarize_eddy_json.py \
  path/to/eddy_info_merge20250101.json \
  --records-csv baseline_records.csv \
  --summary-csv baseline_summary.csv
```

输出：

- 终端打印摘要；
- `baseline_records.csv`：逐个涡旋记录；
- `baseline_summary.csv`：单行汇总统计。

## 3. 默认行为

默认情况下，`records-csv` 只写入被判断为真实识别结果的 eddy，不写入 seed-only 项。

seed-only 项仍会在 summary 中统计为：

```text
seed_only_entries
```

如果希望逐条输出 seed-only 项，可以增加：

```bash
--include-seeds
```

## 4. 主要统计字段

summary 包含：

| 字段 | 说明 |
|---|---|
| `total_entries` | JSON 中识别到的所有 eddy/seed 条目数 |
| `detected_eddies` | 判定为真实涡旋的数量 |
| `seed_only_entries` | 仅 seed、未形成涡旋边界的条目数 |
| `anticyclonic_eddies` | 反气旋涡数量 |
| `cyclonic_eddies` | 气旋涡数量 |
| `mean_radius` | 平均半径，优先使用 effect radius |
| `median_radius` | 半径中位数 |
| `mean_amplitude` | 平均振幅，优先使用 effect amplitude |
| `median_amplitude` | 振幅中位数 |
| `mean_Uavg_max` | 最大平均速度边界对应速度均值 |
| `mean_EKE` | EKE 均值 |

## 5. 字段优先级

为了兼容不同旧输出，脚本使用以下优先级。

### 半径

```text
eddy_effect_radius
  ↓
eddy_shape_radius
  ↓
eddy_Uavg_radius
```

### 振幅

```text
eddy_effect_amp
  ↓
eddy_shape_amp
  ↓
eddy_Uavg_amp
```

## 6. 判定是否为 detected eddy

满足以下任一条件即认为是 detected eddy：

1. `eddy_flag` 为 true；
2. 存在有效的 `eddy_effect_contour`、`eddy_Uavg_contour` 或 `eddy_shape_contour`；
3. 存在非零半径或振幅字段。

这主要是为了兼容历史 JSON 中布尔值、字符串和数值混用的情况。

## 7. 与后续重构的关系

这个脚本的作用是建立 baseline。后续每次重构后，都可以重新运行：

```bash
python scripts/summarize_eddy_json.py new_output.json \
  --records-csv new_records.csv \
  --summary-csv new_summary.csv
```

然后比较：

- 涡旋总数是否一致；
- AE / CE 数量是否一致；
- 半径、振幅是否变化；
- 哪些涡旋被新增或删除。

该脚本本身不应参与涡旋识别流程。
