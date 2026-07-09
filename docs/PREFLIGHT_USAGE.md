# Preflight detection config checks

`scripts/preflight_detection_config.py` 用于在运行识别前做本地预检查。

它不会运行任何涡旋识别算法。

## 1. 基本用法

```bash
python scripts/preflight_detection_config.py configs/example_detection_config.yaml
```

检查内容包括：

```text
Python 环境
NumPy / SciPy / netCDF4 / PyYAML 是否可导入
Basemap / GDAL 是否可导入
input_dir 是否存在
pattern 是否能匹配到输入文件
output_dir 是否存在或父目录是否存在
baseline 文件是否存在
旧代码硬编码风险
```

## 2. 输出 JSON 报告

```bash
python scripts/preflight_detection_config.py \
  configs/example_detection_config.yaml \
  --report-json preflight_report.json
```

## 3. 没有挂载数据时运行

如果当前机器还没有挂载真实输入数据，但你只想检查配置结构和环境，可以使用：

```bash
python scripts/preflight_detection_config.py \
  configs/example_detection_config.yaml \
  --allow-missing-input
```

这样即使 `input_dir` 不存在，也只给 warning，不直接失败。

## 4. 重点 warning 解释

### 4.1 NumPy >= 1.24

旧代码中使用了：

```python
np.float
np.int
```

NumPy 1.24 之后删除了这些别名，因此旧代码可能报错。建议 baseline 阶段使用：

```text
numpy < 1.24
```

### 4.2 Basemap / GDAL 不可导入

旧代码绘图和部分 mask 输出依赖 Basemap / GDAL。如果只运行 JSON 统计工具不一定需要它们，但运行完整 legacy 检测时通常需要。

### 4.3 输入变量名不同

当前 legacy nc 脚本中变量名仍硬编码为：

```text
sla
ugosa
vgosa
```

如果 YAML 配置中写成其他变量名，在 I/O 重构前旧代码不会自动响应。

### 4.4 pool_size 不等于 8

当前 nc 脚本中仍存在：

```python
Pool(processes=8)
```

因此即使 YAML 中设置了其他 `pool_size`，旧代码也不一定会使用。这个问题需要后续低风险修改解决。

## 5. 推荐工作流

```bash
# 1. 检查配置字段
python scripts/validate_detection_config.py configs/example_detection_config.yaml

# 2. 预览 legacy 参数字典
python scripts/config_to_legacy_params.py configs/example_detection_config.yaml \
  --out-json legacy_eddy_select_info.json

# 3. 本地运行前预检查
python scripts/preflight_detection_config.py configs/example_detection_config.yaml \
  --report-json preflight_report.json
```

只有以上步骤都没有 error，才建议进入下一步 wrapper 或 baseline 运行。

## 6. 当前阶段意义

该脚本的作用是提前发现路径、环境和硬编码风险。它本身不应参与涡旋识别算法，也不会改变识别结果。
