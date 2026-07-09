# Guarded explicit execute mode

本文件说明 `scripts/prepare_detection_run.py` 中新增的显式执行模式。

默认行为仍然是 dry-run，不会运行旧算法。

## 1. 默认 dry-run

```bash
python scripts/prepare_detection_run.py configs/example_detection_config.yaml
```

默认只做：

```text
配置校验
legacy 参数预览
preflight 检查
run plan 打印
```

不会导入或调用：

```text
make_eddy_track_AVISO_nc.py
gloabal_eddy_multi_detect()
eddy_main()
collection_loop()
```

## 2. 显式执行模式

只有同时提供下面两个参数，才会尝试运行旧入口函数：

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --execute \
  --confirm-execute
```

执行路径会在最后一步才导入：

```python
make_eddy_track_AVISO_nc
```

并调用：

```python
gloabal_eddy_multi_detect(eddy_select_info)
```

## 3. 为什么需要双确认？

旧算法会：

```text
读取输入数据目录
创建输出目录
生成 JSON
生成 seed JSON
可能生成图像或 mask
进行多进程计算
```

为了避免误运行，必须同时使用：

```text
--execute
--confirm-execute
```

只传 `--execute` 会被拒绝。

## 4. warning 默认阻止执行

即使提供了 `--execute --confirm-execute`，如果存在 validation warning、preflight warning 或参数映射 warning，默认也不会执行。

需要人工确认 warning 后，才可以加：

```bash
--allow-warnings
```

完整形式：

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --execute \
  --confirm-execute \
  --allow-warnings
```

## 5. error 永远阻止执行

以下情况会阻止执行：

```text
validation error
preflight error
缺少 input_dir
没有匹配到输入文件
output_dir 父目录不存在
配置结构错误
```

`--allow-warnings` 不能跳过 error。

## 6. 推荐真实运行前流程

在第一次使用 `--execute` 前，建议完成：

```bash
# 1. 校验配置
python scripts/validate_detection_config.py configs/example_detection_config.yaml

# 2. 预览旧参数
python scripts/config_to_legacy_params.py \
  configs/example_detection_config.yaml \
  --out-json legacy_eddy_select_info.json

# 3. preflight 检查
python scripts/preflight_detection_config.py \
  configs/example_detection_config.yaml \
  --report-json preflight_report.json

# 4. dry-run run plan
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --run-plan-json run_plan.json \
  --legacy-params-json legacy_eddy_select_info.json
```

确认 `run_plan.json` 中：

```text
validation.error_count = 0
preflight.error_count = 0
legacy_params 与旧 GUI/手动参数一致
```

再运行：

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --execute \
  --confirm-execute
```

## 7. 运行后必须做 baseline 对比

真实执行后，应立即使用：

```bash
python scripts/summarize_eddy_json.py \
  path/to/new/eddy_info_mergeYYYYMMDD.json \
  --records-csv new_records.csv \
  --summary-csv new_summary.csv
```

然后与旧结果对比：

```bash
python scripts/compare_eddy_baseline.py summary \
  baseline_summary.csv \
  new_summary.csv \
  --out-csv summary_compare.csv

python scripts/compare_eddy_baseline.py records \
  baseline_records.csv \
  new_records.csv \
  --match-distance-deg 0.25 \
  --out-csv records_compare.csv
```

如果只是 wrapper 接入，理论上结果应与旧流程一致。

## 8. 当前仍未修改算法

本步骤只改 wrapper，不修改：

```text
make_eddy_track_AVISO_nc.py
make_eddy_track_AVISO.py
py_eddy_tracker_classes.py
make_eddy_tracker_list_obj.py
NeighborsSearch.py
haversine_distmat_py.py
```

因此如果执行结果变化，优先检查配置参数是否和旧运行方式完全一致。
