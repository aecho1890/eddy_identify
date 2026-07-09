# Baseline case creation

本文件说明如何建立 baseline case。

baseline case 的目的不是提高识别精度，而是固定一个“原始旧流程结果”，用于后续判断每次重构是否改变了识别结果。

## 1. 本步骤新增内容

```text
scripts/create_baseline_case.py
configs/baseline_cases/south_china_sea_20250101.yaml
configs/baseline_cases/west_pacific_20250101.yaml
configs/baseline_cases/global_20250101.yaml
docs/BASELINE_CASE_CREATION.md
```

## 2. 重要说明

仓库中不包含 AVISO/Copernicus 原始输入数据，也不包含你本地运行生成的 `eddy_info_mergeYYYYMMDD.json`。

因此本 PR 不能直接替你生成真实 baseline 结果文件，但提供了本地建立 baseline 的标准工具和目录结构。

## 3. 推荐 baseline case 顺序

建议依次建立：

| 顺序 | case | 用途 |
|---|---|---|
| 1 | South China Sea | 小区域快速检查，运行压力小 |
| 2 | West Pacific | 多涡旋、多分块、重叠区检查 |
| 3 | Global Ocean | 全流程、0/360° 边界、全球分块检查 |

优先从南海或西太平洋开始，不建议一开始就跑全球。

## 4. 只初始化 baseline case 目录

如果还没有现成 JSON，可以先初始化目录：

```bash
python scripts/create_baseline_case.py \
  --case-name case_wp_20250101 \
  --date 20250101 \
  --region-preset west_pacific \
  --input-dir E:/Data/SLA/nc/2025 \
  --input-file dt_global_allsat_phy_l4_20250101.nc \
  --output-root baseline_runs
```

生成：

```text
baseline_runs/case_wp_20250101/
  input/
  original_output/
  baseline_tables/
  reports/
  case_config.yaml
  notes.md
  commands.md
  manifest.json
```

## 5. 从已有 JSON 建立 baseline

如果你已经用旧代码生成了：

```text
eddy_info_merge20250101.json
```

可以直接建立 baseline 并生成表格：

```bash
python scripts/create_baseline_case.py \
  --case-name case_wp_20250101 \
  --date 20250101 \
  --region-preset west_pacific \
  --input-dir E:/Data/SLA/nc/2025 \
  --input-file dt_global_allsat_phy_l4_20250101.nc \
  --source-json path/to/eddy_info_merge20250101.json \
  --output-root baseline_runs
```

这会复制 JSON 到：

```text
baseline_runs/case_wp_20250101/original_output/eddy_info_merge20250101.json
```

并生成：

```text
baseline_runs/case_wp_20250101/baseline_tables/baseline_records.csv
baseline_runs/case_wp_20250101/baseline_tables/baseline_summary.csv
```

## 6. 覆盖已有 case

如果需要覆盖已有 notes、config、tables：

```bash
python scripts/create_baseline_case.py \
  --case-name case_wp_20250101 \
  --date 20250101 \
  --region-preset west_pacific \
  --input-dir E:/Data/SLA/nc/2025 \
  --source-json path/to/eddy_info_merge20250101.json \
  --output-root baseline_runs \
  --overwrite
```

谨慎使用 `--overwrite`。

## 7. 示例配置文件

新增了三个示例配置：

```text
configs/baseline_cases/south_china_sea_20250101.yaml
configs/baseline_cases/west_pacific_20250101.yaml
configs/baseline_cases/global_20250101.yaml
```

这些配置主要用于记录 case 设计，不会自动被旧代码读取。

实际运行前必须把其中的：

```text
input_dir
input_file
```

改成你本地真实路径。

## 8. 建立 baseline 后怎么用

后续某次新代码生成新结果后，先统计新结果：

```bash
python scripts/summarize_eddy_json.py \
  path/to/new/eddy_info_merge20250101.json \
  --records-csv new_records.csv \
  --summary-csv new_summary.csv
```

再和 baseline 对比：

```bash
python scripts/compare_eddy_baseline.py summary \
  baseline_runs/case_wp_20250101/baseline_tables/baseline_summary.csv \
  new_summary.csv \
  --out-csv summary_compare.csv

python scripts/compare_eddy_baseline.py records \
  baseline_runs/case_wp_20250101/baseline_tables/baseline_records.csv \
  new_records.csv \
  --match-distance-deg 0.25 \
  --out-csv records_compare.csv
```

## 9. baseline 通过标准

如果只是 wrapper、路径或配置接入，理论上应该满足：

```text
detected_eddies 差异 = 0
anticyclonic_eddies 差异 = 0
cyclonic_eddies 差异 = 0
missing_in_new = 0
new_only = 0
```

如果结果不一致，优先检查：

```text
输入文件是否相同
日期是否相同
region.legacy_name 是否相同
z_kernel / m_kernel 是否相同
eddy_pixel_num_range 是否相同
out_range 是否相同
变量单位是否一致
旧代码是否仍走同一个区域硬编码分支
```

## 10. 建议当前先建立的 case

建议你本地先建立：

```text
case_wp_20250101
```

原因：

- 西太平洋涡旋数量相对多；
- 可以检查分块重叠和合并；
- 比全球快；
- 比南海更能暴露问题。

命令模板：

```bash
python scripts/create_baseline_case.py \
  --case-name case_wp_20250101 \
  --date 20250101 \
  --region-preset west_pacific \
  --input-dir E:/Data/SLA/nc/2025 \
  --input-file dt_global_allsat_phy_l4_20250101.nc \
  --source-json path/to/eddy_info_merge20250101.json \
  --output-root baseline_runs
```
