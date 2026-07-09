# Baseline checklist

本清单用于在任何代码重构或算法优化前，建立当前版本的可复现基准结果。

## 1. 为什么必须建立 baseline

当前代码包含多处隐式逻辑：

- SLA 高通滤波参数；
- 局地极值种子点检测；
- 0/360° 经度周期扩展；
- 分块和重叠区设置；
- 闭合等值线筛选；
- shape error 筛选；
- 振幅筛选；
- 最大平均速度边界选择；
- 重叠区重复涡删除。

这些逻辑任何一处微小变化，都可能导致涡旋数量、边界、半径和振幅变化。因此，在重构前必须保存当前版本结果。

## 2. 推荐 baseline 样例

建议至少选三类样例。

| 样例 | 目的 | 建议范围 |
|---|---|---|
| South China Sea | 小区域、快速验证 | 105–125°E, 5–25°N |
| West Pacific | 中等区域、多涡旋场景 | 90–145°E, -20–40°N |
| Global Ocean | 全球分块和 0/360° 边界验证 | 0–360°E, -90–90°N |

## 3. 每个 baseline 应保存的内容

```text
baseline/<case_name>/<YYYYMMDD>/
  input_file.txt
  parameter.json
  eddy_info_mergeYYYYMMDD.json
  seedjson/YYYYMMDD_seed.json
  summary.csv
  runtime.txt
  notes.md
```

## 4. 建议记录的参数

| 参数 | 当前值 | 说明 |
|---|---|---|
| 输入文件 |  | 原始 nc 或 tif 文件路径 |
| 数据变量 | `sla`, `ugosa`, `vgosa` | nc 版本默认变量 |
| 分辨率 | 0.25° | 当前代码中多处硬编码 |
| 经向分块数 |  | GUI 或参数输入 |
| 纬向分块数 |  | GUI 或参数输入 |
| 重叠区宽度 |  | `out_range` |
| Gaussian 经向核 |  | `m_kernel` |
| Gaussian 纬向核 |  | `z_kernel` |
| contour interval | 0.25 cm | `np.arange(seed_sla_min, seed_sla_max, 0.25)` |
| shape error | 55 | 当前固定值 |
| 振幅范围 | 1–150 cm | 当前 `ampmin`, `ampmax` |
| 像素范围 |  | `eddy_pixel_num_range` |
| 进程数 |  | `pool_size` |

## 5. 建议统计指标

每次重构后，至少对比以下指标。

### 5.1 数量指标

| 指标 | baseline | new | difference |
|---|---:|---:|---:|
| total eddies |  |  |  |
| anticyclonic eddies |  |  |  |
| cyclonic eddies |  |  |  |
| inner eddies |  |  |  |
| outer eddies |  |  |  |

### 5.2 属性统计

| 指标 | baseline | new | difference |
|---|---:|---:|---:|
| mean radius |  |  |  |
| median radius |  |  |  |
| mean amplitude |  |  |  |
| median amplitude |  |  |  |
| mean Uavg max |  |  |  |
| mean EKE |  |  |  |

### 5.3 空间一致性

建议后续脚本计算：

- 涡心最近邻距离；
- 同极性匹配数量；
- 半径相对误差；
- 振幅相对误差；
- 边界 IoU；
- 被新增或删除的涡旋列表。

## 6. 允许和不允许的变化

### 文档修改

允许：

- 无输出变化；
- 无算法变化。

### 路径和配置修改

允许：

- 输出路径变化；
- 参数读取方式变化。

不允许：

- 默认参数变化；
- 涡旋数量变化；
- 输出字段名变化。

### I/O 重构

允许：

- 文件读取函数变化。

不允许：

- SLA 数值变化；
- lon/lat 网格偏移；
- u/v 单位变化；
- mask 规则变化。

### 算法优化

允许：

- 结果变化，但必须明确说明变化原因。

必须额外报告：

- 新增涡旋案例；
- 删除涡旋案例；
- 边界明显变化案例；
- 对比图。

## 7. 建议运行记录模板

```text
Date:
Commit:
Input file:
Region:
Parameters:
Runtime:
Python version:
NumPy version:
SciPy version:
GDAL version:
Total eddies:
AE:
CE:
Notes:
```

## 8. 当前阶段说明

本清单只是为后续重构建立检查标准，不改变现有代码运行结果。
