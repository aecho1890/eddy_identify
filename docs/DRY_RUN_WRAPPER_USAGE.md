# Dry-run detection preparation wrapper

`scripts/prepare_detection_run.py` 是一个 dry-run wrapper，用于把前面几个准备工具串起来。

它会做：

```text
读取 YAML 配置
  ↓
校验配置字段
  ↓
转换为 legacy eddy_select_info 字典
  ↓
执行本地 preflight 检查
  ↓
打印运行计划 / 可选写出 run_plan.json
```

它不会做：

```text
导入 make_eddy_track_AVISO_nc.py
调用 gloabal_eddy_multi_detect()
运行 eddy_main()
运行 collection_loop()
生成新的涡旋识别结果
```

## 1. 基本用法

```bash
python scripts/prepare_detection_run.py configs/example_detection_config.yaml
```

终端会显示：

```text
Dry-run detection preparation
-----------------------------
will_execute_detection: False
validation_errors: ...
validation_warnings: ...
preflight_errors: ...
preflight_warnings: ...
```

并打印 legacy 参数预览，例如：

```text
inputfile
outfile
z_block_num
m_block_num
out_range
z_kernel
m_kernel
pool_size
eddy_pixel_num_range
eddy_location
```

## 2. 写出 run plan JSON

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --run-plan-json run_plan.json
```

`run_plan.json` 中包含：

```text
mode: dry_run_only
will_execute_detection: false
validation messages
legacy_params
preflight report
known_blockers_before_real_execution
```

## 3. 同时写出 legacy 参数 JSON

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --run-plan-json run_plan.json \
  --legacy-params-json legacy_eddy_select_info.json
```

这样可以把旧代码需要的参数字典单独保存下来，方便人工检查。

## 4. 没有挂载输入数据时

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --allow-missing-input
```

这会把缺少输入目录或匹配文件的问题降为 warning，用于没有挂载数据的开发机。

## 5. strict 模式

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --strict
```

在 strict 模式下，validation warning 也会导致非零退出码。

## 6. 与前面工具的关系

这个 wrapper 等价于集中运行：

```bash
python scripts/validate_detection_config.py configs/example_detection_config.yaml
python scripts/config_to_legacy_params.py configs/example_detection_config.yaml
python scripts/preflight_detection_config.py configs/example_detection_config.yaml
```

但它不会替代 `summarize_eddy_json.py` 和 `compare_eddy_baseline.py`，因为这两个工具用于已有结果的 baseline 统计和对比。

## 7. 为什么仍不执行识别？

当前 legacy 代码仍有若干硬编码：

```text
NetCDF 变量名固定为 sla / ugosa / vgosa
经纬度分辨率多处固定为 0.25°
Pool(processes=8) 有硬编码
部分区域名对应内部硬编码范围
滤波方法固定为 Gaussian high-pass
```

因此，在没有建立 baseline 前，不应让 wrapper 直接调用旧算法。否则如果结果变化，很难判断是配置问题、I/O 问题还是算法变化。

## 8. 下一步

建议先完成以下本地工作：

```text
1. 用现有旧代码跑一个固定日期 case
2. 保存 eddy_info_mergeYYYYMMDD.json
3. 用 summarize_eddy_json.py 生成 baseline_summary.csv 和 baseline_records.csv
4. 用 prepare_detection_run.py 检查配置和 legacy 参数是否对应当前旧运行参数
```

之后才建议开新的 PR 增加显式 `--execute` 模式，而且默认仍应是 dry-run。
