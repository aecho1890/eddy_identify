# Config to legacy parameter preview

`scripts/config_to_legacy_params.py` 用于把新的 YAML 配置模板转换为旧代码使用的 `eddy_select_info` 字典。

当前阶段它只是预览工具：

```text
读取 YAML
  ↓
生成 legacy eddy_select_info 字典
  ↓
打印到终端或保存为 JSON
```

它不会：

```text
导入 make_eddy_track_AVISO_nc.py
调用 gloabal_eddy_multi_detect()
运行 eddy_main()
运行 collection_loop()
修改任何识别结果
```

## 1. 基本用法

```bash
python scripts/config_to_legacy_params.py configs/example_detection_config.yaml
```

会打印类似：

```json
{
  "inputfile": "./data/input/",
  "outfile": "./data/output/",
  "z_block_num": 1,
  "m_block_num": 1,
  "out_range": 3.0,
  "z_kernel": 6.0,
  "m_kernel": 6.0,
  "pool_size": 8,
  "eddy_pixel_num_range": [2, 10000],
  "eddy_location": "Global Ocean"
}
```

## 2. 保存为 JSON

```bash
python scripts/config_to_legacy_params.py \
  configs/example_detection_config.yaml \
  --out-json legacy_eddy_select_info.json
```

生成的 `legacy_eddy_select_info.json` 可用于人工检查或后续 wrapper 开发。

## 3. 字段映射关系

| YAML 配置字段 | legacy key | 说明 |
|---|---|---|
| `input.input_dir` | `inputfile` | 输入目录 |
| `output.output_dir` | `outfile` | 输出目录 |
| `blocking.lat_block` | `z_block_num` | 纬向分块数 |
| `blocking.lon_block` | `m_block_num` | 经向分块数 |
| `blocking.outer_range` | `out_range` | 分块重叠宽度 |
| `filter.z_kernel` | `z_kernel` | 纬向 Gaussian kernel |
| `filter.m_kernel` | `m_kernel` | 经向 Gaussian kernel |
| `blocking.pool_size` | `pool_size` | 并行进程数 |
| `eddy_detection.pixel_num_min/max` | `eddy_pixel_num_range` | 涡旋像素数范围 |
| `region.legacy_name` | `eddy_location` | 旧代码中的区域名称 |
| `plot.line_width` | `line_width` | 绘图线宽 |
| `plot.dpi` | `dpi` | 绘图分辨率 |

## 4. legacy 区域名

当前旧代码中存在硬编码区域分支，因此 `region.legacy_name` 必须谨慎设置。

常见值：

```text
Global Ocean
South China Sea
West Pacific
North Indian Ocean
Specific area
Kuroshio Current
```

注意：

- 如果是 `Global Ocean`，旧代码一般走全球默认分块；
- 如果是 `South China Sea`，旧代码内部会使用硬编码南海范围；
- 如果是 `West Pacific`，旧代码内部会使用硬编码西太平洋范围；
- 如果是 `Specific area`，旧代码目前也有硬编码坐标，不等于任意用户输入区域。

因此在真正运行前，不应简单认为 YAML 中的 `lon_min/lon_max/lat_min/lat_max` 已经控制了旧代码区域。

## 5. 为什么暂时不直接运行识别？

因为当前旧入口函数中仍存在若干硬编码逻辑：

```text
NetCDF 变量名固定为 sla / ugosa / vgosa
经纬度网格固定为 0.25°
多个区域名对应硬编码范围
Pool(processes=8) 有硬编码
滤波方法固定为 Gaussian high-pass
```

如果直接把配置接入并运行，很容易造成“看起来配置改了，但实际旧代码没有完全响应配置”的问题。

因此当前阶段只做转换预览。

## 6. 后续安全迁移步骤

建议顺序：

```text
Step 1: validate_detection_config.py 检查 YAML
Step 2: config_to_legacy_params.py 生成 eddy_select_info 预览
Step 3: 人工确认 legacy JSON 与当前 GUI/手动参数一致
Step 4: 新增 dry-run wrapper，打印即将运行的参数
Step 5: 在 baseline case 上运行旧算法
Step 6: 使用 summarize 和 compare 工具确认结果一致
Step 7: 再考虑修改核心代码内部硬编码
```

## 7. 当前阶段判断标准

当前脚本输出正确即可，不应期待它生成新涡旋结果。

如果输出中 `_warnings` 非空，应先处理 warning，再进入下一步。
