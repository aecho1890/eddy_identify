# Refactor preparation progress

本文件记录当前谨慎重构准备工作的实际进度。

## 当前分支

```text
refactor-step-1-docs
```

## 当前 PR

```text
PR #1: Step 1-3: add docs, environment notes, and baseline tools
```

## 已完成内容

## Step 1：文档和环境说明

新增：

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

## 当前未修改的算法文件

以下文件在当前 PR 中不应被修改：

```text
make_eddy_track_AVISO_nc.py
make_eddy_track_AVISO.py
py_eddy_tracker_classes.py
make_eddy_tracker_list_obj.py
NeighborsSearch.py
haversine_distmat_py.py
```

## 推荐下一步

下一步建议进入 Step 4：新增一个最小 baseline 运行说明和本地操作流程，但仍不修改核心算法。

建议新增：

```text
docs/BASELINE_WORKFLOW.md
```

该文档应说明：

1. 如何选取一个固定日期输入文件；
2. 如何运行原始识别脚本；
3. 如何用 `summarize_eddy_json.py` 生成 baseline；
4. 如何用 `compare_eddy_baseline.py` 对比后续结果。

在完成 baseline 文档后，才建议进入低风险代码层修改，例如配置文件化或新增 reader，不建议直接修改 `make_eddy_track_AVISO_nc.py`。
