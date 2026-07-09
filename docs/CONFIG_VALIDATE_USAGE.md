# Config validation tool

`scripts/validate_detection_config.py` 是一个只读配置检查工具。它只读取 YAML 配置文件，检查字段是否完整、类型是否合理、参数范围是否明显异常。

它不会：

```text
导入 make_eddy_track_AVISO_nc.py
调用 gloabal_eddy_multi_detect()
运行涡旋识别
修改任何输出文件
改变任何算法结果
```

## 1. 基本用法

```bash
python scripts/validate_detection_config.py configs/example_detection_config.yaml
```

如果配置结构正常，会打印：

```text
Detection config validation
---------------------------
errors: 0
warnings: 0
```

如果有问题，会输出 `ERROR` 或 `WARNING`。

## 2. 输出 JSON 报告

```bash
python scripts/validate_detection_config.py \
  configs/example_detection_config.yaml \
  --report-json config_validation_report.json
```

输出文件包含：

```text
summary
messages
error_count
warning_count
```

## 3. strict 模式

默认情况下，只有 `ERROR` 会导致非零退出码。

如果希望 `WARNING` 也导致非零退出码，可使用：

```bash
python scripts/validate_detection_config.py \
  configs/example_detection_config.yaml \
  --strict
```

## 4. 检查内容

当前检查：

### 4.1 顶层 section

必须包含：

```text
project
input
output
region
blocking
filter
eddy_detection
merge
baseline
```

### 4.2 input

检查：

```text
input.input_dir
input.file_type
input.pattern
input.variables.sla
input.variables.u
input.variables.v
input.longitude_convention
```

允许的 `file_type`：

```text
nc
tif
auto
```

允许的 `longitude_convention`：

```text
0_360
-180_180
```

### 4.3 filter

允许的 `filter.method`：

```text
gaussian_highpass
bessel_highpass
```

其中 `bessel_highpass` 当前只是未来选项，legacy 代码尚未启用。

### 4.4 eddy_detection

检查：

```text
contour_interval_cm
shape_error
amplitude_min_cm
amplitude_max_cm
detect_anticyclonic
detect_cyclonic
```

并检查：

```text
amplitude_min_cm < amplitude_max_cm
```

### 4.5 region

检查：

```text
dlon > 0
dlat > 0
lon_min < lon_max
lat_min < lat_max
lat_min / lat_max 是否在 [-90, 90]
```

### 4.6 merge

检查：

```text
center_distance_threshold_deg
boundary_iou_threshold
duplicate_policy
```

允许的 `duplicate_policy`：

```text
keep_larger_amplitude
keep_first
keep_last
```

## 5. 依赖

该脚本需要：

```text
PyYAML
```

安装方式：

```bash
pip install pyyaml
```

或者在 conda 环境中安装：

```bash
conda install -c conda-forge pyyaml
```

## 6. 后续作用

这个工具为后续配置化做准备。

推荐迁移路线：

```text
Step A：validate_detection_config.py 只检查配置
Step B：新增 wrapper，把配置转换为 eddy_select_info
Step C：wrapper 调用旧函数，但核心函数不变
Step D：确认 baseline 完全一致
Step E：再逐步去掉核心函数内部硬编码
```

当前只完成 Step A。
