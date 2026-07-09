# Step 11 guarded execute wrapper progress

当前分支：

```text
refactor-step-11-explicit-execute-wrapper
```

该分支基于：

```text
refactor-step-10-dry-run-wrapper
```

因此它依赖：

```text
Step 1–9 preparation layer
Step 10 dry-run wrapper
```

## 本分支修改内容

更新：

```text
scripts/prepare_detection_run.py
```

新增：

```text
docs/EXPLICIT_EXECUTE_WRAPPER_USAGE.md
docs/STEP11_EXECUTE_PROGRESS.md
```

## 新增能力

`prepare_detection_run.py` 新增显式执行模式：

```bash
python scripts/prepare_detection_run.py \
  configs/example_detection_config.yaml \
  --execute \
  --confirm-execute
```

默认仍然是 dry-run。

## 安全保护

### 1. 默认不执行

不传 `--execute` 时，只生成 run plan，不调用旧算法。

### 2. 必须双确认

只传 `--execute` 不会运行，必须同时传：

```text
--execute
--confirm-execute
```

### 3. error 永远阻止执行

以下情况会阻止执行：

```text
validation error
preflight error
```

### 4. warning 默认阻止执行

如果存在 warning，默认也阻止执行。

必须人工确认后加：

```text
--allow-warnings
```

## 算法影响

本分支没有修改任何核心算法文件。

未修改：

```text
make_eddy_track_AVISO_nc.py
make_eddy_track_AVISO.py
py_eddy_tracker_classes.py
make_eddy_tracker_list_obj.py
NeighborsSearch.py
haversine_distmat_py.py
```

## 执行路径

只有在显式执行模式下，才会在函数内部动态导入：

```python
make_eddy_track_AVISO_nc
```

并调用：

```python
gloabal_eddy_multi_detect(eddy_select_info)
```

## 运行后要求

任何真实执行后，必须立即做 baseline 对比：

```text
summarize_eddy_json.py
compare_eddy_baseline.py
```

如果只是 wrapper 接入，理论上结果应与原始旧流程一致。

## 下一步建议

不要继续在本分支修改算法。

后续建议单独开 PR 处理低风险硬编码问题，例如：

```text
Pool(processes=8) 使用 eddy_select_info['pool_size']
```

但这类修改已经属于会影响运行行为的代码修改，必须在 baseline case 建立后进行。
