# Refactor preparation progress

本文件记录当前谨慎重构准备工作的实际进度。

## 当前分支

```text
refactor-step-1-docs
```

## 当前 PR

```text
PR #1: Step 1-9: safe refactor preparation without algorithm changes
```

## 总体原则

当前 PR 的所有修改都属于准备工作：

```text
文档
环境说明
baseline 统计
baseline 对比
配置模板
配置校验
配置到 legacy 参数预览
本地预检查
.gitignore 防误提交
```

算法影响：无。

## Step 1：文档和环境说明

新增 / 更新：

```text
README.md
environment.yml
docs/REFACTOR_PLAN.md
docs/BASELINE_CHECKLIST.md
```

作用：

- 梳理当前代码框架；
- 记录 legacy 依赖风险；
- 明确高风险核心函数；
- 建立 baseline 检查原则。

算法影响：无。

## Step 2：只读 JSON 统计工具

新增：

```text
scripts/summarize_eddy_json.py
docs/JSON_SUMMARY_USAGE.md
```

作用：

- 读取已有 `eddy_info_mergeYYYYMMDD.json`；
- 输出逐涡旋 records CSV；
- 输出总体 summary CSV；
- 兼容扁平 JSON 和 `inner/outer/Block` 嵌套 JSON。

算法影响：无。

## Step 3：baseline 对比工具

新增：

```text
scripts/compare_eddy_baseline.py
docs/BASELINE_COMPARE_USAGE.md
```

作用：

- 比较两个 summary CSV；
- 比较两个 records CSV；
- 判断重构前后涡旋数量、AE/CE、半径、振幅是否变化；
- 标记 `matched`、`missing_in_new`、`new_only` 涡旋。

算法影响：无。

## Step 4：完整 baseline 工作流

新增：

```text
docs/BASELINE_WORKFLOW.md
```

作用：

- 说明如何选择 baseline case；
- 说明如何保存原始 JSON；
- 说明如何生成 records / summary；
- 说明如何比较后续新结果。

算法影响：无。

## Step 5：配置模板和字段说明

新增 / 更新：

```text
configs/example_detection_config.yaml
docs/CONFIG_FIELDS.md
```

作用：

- 统一未来参数命名；
- 记录 input / output / region / blocking / filter / eddy_detection / merge / baseline 等字段；
- 明确该配置当前只是模板，旧代码不会自动读取。

算法影响：无。

## Step 6：只读配置校验工具

新增：

```text
scripts/validate_detection_config.py
docs/CONFIG_VALIDATE_USAGE.md
```

更新：

```text
environment.yml
```

作用：

- 检查 YAML section 是否完整；
- 检查字段类型和范围；
- 输出可选 JSON 报告；
- 增加 `pyyaml` 依赖。

算法影响：无。

## Step 7：配置到 legacy 参数预览

新增：

```text
scripts/config_to_legacy_params.py
docs/CONFIG_TO_LEGACY_USAGE.md
```

更新：

```text
configs/example_detection_config.yaml
```

作用：

- 将 YAML 配置转换为旧代码使用的 `eddy_select_info` 字典预览；
- 显式映射 `inputfile`、`outfile`、`z_block_num`、`m_block_num`、`out_range`、`z_kernel`、`m_kernel`、`pool_size`、`eddy_pixel_num_range`、`eddy_location` 等字段；
- 只打印或写 JSON，不调用识别函数。

算法影响：无。

## Step 8：本地运行前预检查

新增：

```text
scripts/preflight_detection_config.py
docs/PREFLIGHT_USAGE.md
```

作用：

- 检查 Python / NumPy / SciPy / netCDF4 / PyYAML；
- 检查 Basemap / GDAL 是否可导入；
- 检查输入目录和文件匹配；
- 检查输出目录状态；
- 提醒旧代码硬编码风险，例如变量名和 `Pool(processes=8)`。

算法影响：无。

## Step 9：防止误提交大文件和结果文件

新增：

```text
.gitignore
```

作用：

- 忽略 raw data、NetCDF、GeoTIFF、baseline 输出、比较表格、临时报告、运行结果和缓存；
- 避免后续把大数据或结果文件误提交到 GitHub。

算法影响：无。

## 当前未修改的算法文件

以下文件在当前 PR 中未修改：

```text
make_eddy_track_AVISO_nc.py
make_eddy_track_AVISO.py
py_eddy_tracker_classes.py
make_eddy_tracker_list_obj.py
NeighborsSearch.py
haversine_distmat_py.py
```

## 推荐下一步

在合并本 PR 前，建议人工检查新增脚本和文档。

合并后，再进入下一个独立 PR：

```text
Step 10：新增 dry-run wrapper
```

该 wrapper 可以读取配置、生成 legacy 参数、打印即将运行的命令和风险提示，但默认仍不调用识别算法。

只有在 baseline 建立完成后，才建议开启真正运行模式或修改 `make_eddy_track_AVISO_nc.py`。 
