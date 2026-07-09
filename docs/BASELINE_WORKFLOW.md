# Baseline workflow before refactoring

本文档说明在修改任何核心识别算法前，如何建立当前版本的 baseline。baseline 的目的不是提升结果，而是回答一个最基本的问题：

> 后续某次修改是否改变了涡旋识别结果？如果改变了，具体改变在哪里？

当前 workflow 只使用新增的只读工具，不修改任何识别算法文件。

## 1. 推荐目录结构

建议在本地项目外部或项目根目录下建立 baseline 工作目录。

```text
baseline_runs/
  case_scs_20250101/
    input/
    original_output/
    baseline_tables/
    notes.md
  case_wp_20250101/
    input/
    original_output/
    baseline_tables/
    notes.md
```

其中：

| 目录 | 作用 |
|---|---|
| `input/` | 保存或记录原始输入文件路径 |
| `original_output/` | 保存原始算法输出 JSON |
| `baseline_tables/` | 保存 summary、records 和后续 compare 结果 |
| `notes.md` | 记录运行参数、环境和异常情况 |

## 2. 建议至少建立三个 baseline case

| case | 目的 | 建议范围 |
|---|---|---|
| `case_scs_YYYYMMDD` | 快速小区域检查 | 南海，例如 105–125°E, 5–25°N |
| `case_wp_YYYYMMDD` | 多涡旋区域检查 | 西北太平洋，例如 90–145°E, -20–40°N |
| `case_global_YYYYMMDD` | 全球分块和 0/360° 边界检查 | 全球 |

如果暂时没有区域裁剪流程，可以先用当前代码支持的原始输入和原始输出建立 baseline。

## 3. 记录输入数据

每个 case 建议记录：

```text
input_file:
file_date:
data_source:
variables:
  sla:
  u:
  v:
grid_resolution:
region:
```

对于当前 `.nc` 版本，代码默认变量一般是：

```text
sla
ugosa
vgosa
```

需要特别注意单位：

- SLA 在代码内部存在 cm 与 m 的历史混用风险；
- u/v 在部分诊断量计算时出现 `/100`，需要后续重点检查；
- 不要在 baseline 建立阶段改变单位。

## 4. 运行原始识别代码

当前核心入口在：

```text
make_eddy_track_AVISO_nc.py
```

主要入口函数是：

```python
gloabal_eddy_multi_detect(eddy_select_info)
```

注意：函数名中 `gloabal` 是历史拼写，baseline 阶段不要改名。

在运行时，需要记录 `eddy_select_info` 中的关键参数，例如：

```text
inputdirectory:
outdir:
lon_block:
lat_block:
outer_range:
eddy_pixel_num_range:
z_kernel:
m_kernel:
pool_size:
```

如果当前是通过 GUI 或已有脚本运行，请保持原运行方式不变，先不要改命令行接口。

## 5. 保存原始输出

运行完成后，把核心 JSON 输出复制到 case 目录，例如：

```text
baseline_runs/case_wp_20250101/original_output/eddy_info_merge20250101.json
```

如果有 seed JSON，也建议保存：

```text
baseline_runs/case_wp_20250101/original_output/seed_20250101.json
```

如果有 mask 或 jpg，也建议保存，但只读统计工具主要使用 JSON。

## 6. 生成 baseline summary 和 records

使用：

```bash
python scripts/summarize_eddy_json.py \
  baseline_runs/case_wp_20250101/original_output/eddy_info_merge20250101.json \
  --records-csv baseline_runs/case_wp_20250101/baseline_tables/baseline_records.csv \
  --summary-csv baseline_runs/case_wp_20250101/baseline_tables/baseline_summary.csv
```

生成：

```text
baseline_records.csv
baseline_summary.csv
```

其中：

| 文件 | 作用 |
|---|---|
| `baseline_records.csv` | 每个涡旋一行，包含涡心、极性、半径、振幅等 |
| `baseline_summary.csv` | 单行汇总，包含总数、AE、CE、平均半径、平均振幅等 |

## 7. 后续修改后生成 new summary 和 records

当后续某个新分支运行出新结果后，使用同样命令生成：

```bash
python scripts/summarize_eddy_json.py \
  new_runs/case_wp_20250101/output/eddy_info_merge20250101.json \
  --records-csv new_runs/case_wp_20250101/tables/new_records.csv \
  --summary-csv new_runs/case_wp_20250101/tables/new_summary.csv
```

注意：必须使用同一天、同一输入、同一区域、同一参数。

## 8. 比较 summary

快速比较总体统计：

```bash
python scripts/compare_eddy_baseline.py summary \
  baseline_runs/case_wp_20250101/baseline_tables/baseline_summary.csv \
  new_runs/case_wp_20250101/tables/new_summary.csv \
  --out-csv new_runs/case_wp_20250101/tables/summary_compare.csv
```

如果只是文档、环境或路径整理，理论上以下指标应完全一致：

```text
detected_eddies
anticyclonic_eddies
cyclonic_eddies
mean_radius
median_radius
mean_amplitude
median_amplitude
```

## 9. 比较逐涡旋 records

逐涡旋匹配：

```bash
python scripts/compare_eddy_baseline.py records \
  baseline_runs/case_wp_20250101/baseline_tables/baseline_records.csv \
  new_runs/case_wp_20250101/tables/new_records.csv \
  --match-distance-deg 0.25 \
  --out-csv new_runs/case_wp_20250101/tables/records_compare.csv
```

重点查看：

```text
matched
missing_in_new
new_only
```

如果只是非算法重构，应满足：

```text
missing_in_new = 0
new_only = 0
```

## 10. 建议 notes.md 模板

每个 case 建议保存一份 `notes.md`。

```markdown
# Baseline notes

## Case

- case_name:
- date:
- region:
- input_file:

## Environment

- OS:
- Python:
- NumPy:
- SciPy:
- GDAL:
- netCDF4:

## Parameters

- lon_block:
- lat_block:
- outer_range:
- eddy_pixel_num_range:
- z_kernel:
- m_kernel:
- pool_size:

## Output

- output_json:
- seed_json:
- mask:
- figures:

## Summary

- detected_eddies:
- anticyclonic_eddies:
- cyclonic_eddies:
- mean_radius:
- mean_amplitude:

## Notes

- Any warning:
- Any manual operation:
- Any known issue:
```

## 11. baseline 通过标准

### 11.1 文档修改

应满足：

```text
不需要重新运行识别；算法结果不应变化。
```

### 11.2 路径配置化

应满足：

```text
detected_eddies 差异 = 0
AE 差异 = 0
CE 差异 = 0
missing_in_new = 0
new_only = 0
```

### 11.3 I/O 重构

除上述指标外，还必须检查：

```text
core_lon 是否整体偏移
core_lat 是否整体偏移
radius 是否整体放大或缩小
amplitude 是否整体放大或缩小
```

### 11.4 算法优化

允许结果变化，但必须解释：

```text
为什么新增涡旋
为什么删除涡旋
半径为什么变化
振幅为什么变化
是否更接近 py-eddy-tracker 或人工检查结果
```

## 12. 当前建议

在完成本 workflow 后，下一步可以进行低风险代码准备：

1. 新增 `configs/example_detection_config.yaml`；
2. 新增 `docs/CONFIG_FIELDS.md`；
3. 先不让旧核心代码读取配置文件；
4. 等 baseline 完成后，再逐步把路径和参数迁移到配置文件。

这可以避免直接修改 `make_eddy_track_AVISO_nc.py` 导致结果不可控。
