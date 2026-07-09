# Step 10 dry-run wrapper progress

当前分支：

```text
refactor-step-10-dry-run-wrapper
```

该分支基于：

```text
refactor-step-1-docs
```

因此它依赖 Step 1–9 的准备层。

## 本分支新增内容

```text
scripts/prepare_detection_run.py
docs/DRY_RUN_WRAPPER_USAGE.md
docs/STEP10_DRY_RUN_PROGRESS.md
```

## 作用

`prepare_detection_run.py` 将以下准备工具串联起来：

```text
validate_detection_config.py
config_to_legacy_params.py
preflight_detection_config.py
```

它会生成：

```text
validation report
legacy eddy_select_info preview
preflight report
run plan
```

## 明确不做的事情

当前分支不会：

```text
导入 make_eddy_track_AVISO_nc.py
调用 gloabal_eddy_multi_detect()
调用 eddy_main()
调用 collection_loop()
修改任何算法文件
生成新的涡旋识别结果
```

## 设计原因

在真正执行旧算法前，需要先确认：

1. YAML 配置字段正确；
2. YAML 转换出的 legacy 参数与当前手动/GUI 运行参数一致；
3. 本地环境和输入路径可用；
4. 至少一个 baseline case 已经保存；
5. 后续执行结果可以用 baseline 工具对比。

## 当前状态

算法影响：无。

修改范围：仅新增 dry-run wrapper 和文档。

## 下一步建议

不要在本分支直接加入真实执行模式。

建议顺序：

```text
1. 合并 Step 1–9 准备层
2. 合并 Step 10 dry-run wrapper
3. 本地建立至少一个 baseline case
4. 新开 Step 11 PR：增加显式 --execute 模式，但默认仍 dry-run
5. 用 baseline 工具验证执行结果是否与旧流程一致
```
