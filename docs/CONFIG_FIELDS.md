# Configuration fields

`configs/example_detection_config.yaml` 是后续路径和参数配置化的模板。当前阶段它只是模板，旧版识别代码还不会读取该文件。

## 1. 使用原则

当前阶段：

```text
配置文件不参与运行
配置文件不改变结果
配置文件只用于统一未来参数命名
```

后续真正让代码读取配置文件前，必须先完成 baseline 对照。

## 2. project

```yaml
project:
  name: eddy_identify
  description: "..."
```

用于记录项目名称和说明，不影响算法。

## 3. input

```yaml
input:
  input_dir: "./data/input"
  file_type: "nc"
  pattern: "*.nc"
  variables:
    sla: "sla"
    u: "ugosa"
    v: "vgosa"
  longitude_convention: "0_360"
```

字段说明：

| 字段 | 说明 |
|---|---|
| `input_dir` | 输入文件目录 |
| `file_type` | 输入格式，未来支持 `nc`、`tif`、`auto` |
| `pattern` | 文件匹配规则 |
| `variables.sla` | NetCDF 中 SLA 变量名 |
| `variables.u` | NetCDF 中纬向/经向地转流变量名，当前常用 `ugosa` |
| `variables.v` | NetCDF 中另一速度分量变量名，当前常用 `vgosa` |
| `longitude_convention` | 经度格式，例如 `0_360` 或 `-180_180` |

注意：当前 `make_eddy_track_AVISO_nc.py` 中默认变量是：

```text
sla
ugosa
vgosa
```

## 4. output

```yaml
output:
  output_dir: "./data/output"
  write_json: true
  write_records_csv: true
  write_summary_csv: true
  write_geojson: false
  write_mask: false
  write_figures: false
```

字段说明：

| 字段 | 说明 |
|---|---|
| `output_dir` | 输出目录 |
| `write_json` | 是否保存 legacy JSON |
| `write_records_csv` | 是否保存逐涡旋表格 |
| `write_summary_csv` | 是否保存汇总表格 |
| `write_geojson` | 未来是否输出 GeoJSON |
| `write_mask` | 未来是否输出 mask |
| `write_figures` | 未来是否输出图像 |

当前旧版程序主要输出 JSON、部分图像和 mask。CSV 由只读工具生成。

## 5. region

```yaml
region:
  lon_min: null
  lon_max: null
  lat_min: null
  lat_max: null
  dlon: 0.25
  dlat: 0.25
```

字段说明：

| 字段 | 说明 |
|---|---|
| `lon_min` | 区域最小经度，`null` 表示不裁剪 |
| `lon_max` | 区域最大经度 |
| `lat_min` | 区域最小纬度 |
| `lat_max` | 区域最大纬度 |
| `dlon` | 经度分辨率 |
| `dlat` | 纬度分辨率 |

当前旧代码多处假设 0.25° 分辨率，因此 baseline 前不要随意改分辨率。

## 6. blocking

```yaml
blocking:
  lon_block: 1
  lat_block: 1
  outer_range: 3.0
  pool_size: 8
```

字段说明：

| 字段 | 说明 |
|---|---|
| `lon_block` | 经向分块数 |
| `lat_block` | 纬向分块数 |
| `outer_range` | 分块重叠宽度，对应旧代码中的 `outer_range` |
| `pool_size` | 并行进程数 |

注意：当前 nc 版本中有一处 `Pool(processes=8)` 硬编码。后续配置化时需要单独修改并验证。

## 7. filter

```yaml
filter:
  method: "gaussian_highpass"
  z_kernel: 6
  m_kernel: 6
  bessel_cutoff_km: 500
```

字段说明：

| 字段 | 说明 |
|---|---|
| `method` | 当前 legacy 方法是 Gaussian high-pass |
| `z_kernel` | 纬向 Gaussian kernel 参数 |
| `m_kernel` | 经向 Gaussian kernel 参数 |
| `bessel_cutoff_km` | 未来可用于 py-eddy-tracker 风格 Bessel 滤波 |

当前旧方法：

```python
sla_filtered = sla - gaussian_filter(sla, [z_kernel, m_kernel])
```

不要在 baseline 前切换滤波方法。

## 8. eddy_detection

```yaml
eddy_detection:
  contour_interval_cm: 0.25
  shape_error: 55
  amplitude_min_cm: 1.0
  amplitude_max_cm: 150.0
  pixel_num_min: null
  pixel_num_max: null
  detect_anticyclonic: true
  detect_cyclonic: true
```

字段说明：

| 字段 | 说明 |
|---|---|
| `contour_interval_cm` | 等值线间隔，旧代码使用 0.25 cm |
| `shape_error` | shape error 阈值 |
| `amplitude_min_cm` | 最小振幅 |
| `amplitude_max_cm` | 最大振幅 |
| `pixel_num_min` | 最小像素数 |
| `pixel_num_max` | 最大像素数 |
| `detect_anticyclonic` | 是否识别反气旋 |
| `detect_cyclonic` | 是否识别气旋 |

这些字段都直接影响涡旋数量，后续修改必须与 baseline 对比。

## 9. merge

```yaml
merge:
  center_distance_threshold_deg: 0.5
  duplicate_policy: "keep_larger_amplitude"
  use_boundary_iou: false
  boundary_iou_threshold: 0.5
```

字段说明：

| 字段 | 说明 |
|---|---|
| `center_distance_threshold_deg` | 重叠区重复涡判断距离阈值 |
| `duplicate_policy` | 重复涡保留策略 |
| `use_boundary_iou` | 未来是否使用边界 IoU 辅助去重 |
| `boundary_iou_threshold` | 边界 IoU 阈值 |

当前旧逻辑主要是：涡心接近时，保留振幅较大的涡。

## 10. baseline

```yaml
baseline:
  baseline_json: null
  baseline_records_csv: null
  baseline_summary_csv: null
  match_distance_deg: 0.25
```

用于记录 baseline 文件和匹配阈值，不影响算法。

## 11. 迁移建议

后续真正配置化时，建议分三步：

### Step A：只读取配置并打印

新增一个脚本读取 YAML 并打印参数，不调用识别函数。

### Step B：配置驱动新增 wrapper

新增 wrapper，把配置转成旧函数需要的 `eddy_select_info`，但不修改核心函数。

### Step C：核心函数内部逐步去硬编码

只有在 Step B 的输出和 baseline 一致后，才进入核心函数内部去硬编码。

## 12. 禁止事项

在没有 baseline 前，不建议：

- 改 `shape_error`；
- 改 `contour_interval_cm`；
- 改 `amplitude_min_cm`；
- 改 `z_kernel` / `m_kernel`；
- 改 `outer_range`；
- 改经纬度网格构造方式；
- 改 u/v 单位处理。
