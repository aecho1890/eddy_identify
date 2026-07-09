# Cautious refactor plan

本文件记录后续重构原则和顺序。核心原则是：**先保证当前结果可复现，再逐步整理工程结构；任何一步都不应在没有对照结果的情况下修改识别算法。**

## 1. 重构原则

### 1.1 不直接大改核心算法

以下函数暂时视为高风险核心函数：

- `gloabal_eddy_multi_detect()`
- `eddy_main()`
- `collection_loop()`
- `eddyjson_merge()`
- `eddyjson_outer()`
- `reject()`
- `lon_lat_block()`

第一阶段不修改这些函数内部逻辑。

### 1.2 每一步都要可回退

所有修改应通过独立分支和 pull request 完成。每个 PR 只做一类事情，例如：

- 只加文档；
- 只加基准测试脚本；
- 只替换路径拼接；
- 只抽取读取函数；
- 只抽取输出函数。

### 1.3 先保持结果一致，再考虑优化

重构前后至少比较：

- 涡旋总数；
- 反气旋数量；
- 气旋数量；
- 平均半径；
- 平均振幅；
- 涡心位置差异；
- 识别边界差异；
- 输出文件结构是否一致。

## 2. 推荐阶段

## Phase 0：基准建立

目标：保存当前代码在固定输入上的标准输出。

建议至少选择三组样例：

1. 单日南海区域；
2. 单日西北太平洋区域；
3. 单日全球数据。

每组样例保存：

```text
baseline/
  south_china_sea/YYYYMMDD/
  west_pacific/YYYYMMDD/
  global/YYYYMMDD/
```

每个目录下保存：

```text
input_file.txt
parameter.json
eddy_info_mergeYYYYMMDD.json
summary.csv
runtime.txt
```

## Phase 1：文档和环境整理

已开始。

只新增：

- `README.md`
- `environment.yml`
- `docs/REFACTOR_PLAN.md`
- `docs/BASELINE_CHECKLIST.md`

不修改任何 `.py` 文件。

## Phase 2：只读检查脚本

新增一个脚本，用于读取输出 JSON 并统计结果，但不重新识别涡旋。

建议文件：

```text
scripts/summarize_eddy_json.py
```

功能：

- 读取 `eddy_info_mergeYYYYMMDD.json`；
- 统计 AE / CE 数量；
- 统计半径、振幅、平均速度；
- 输出 CSV。

该脚本不改变旧结果，只用于对照。

## Phase 3：路径和参数配置化

低风险修改目标：

- 用 `pathlib.Path` 替换部分 Windows 路径拼接；
- 保留原有默认参数；
- 增加配置读取，但不改变旧函数参数。

不要一次性替换全仓库路径，应先从新增脚本开始，再逐步进入核心文件。

## Phase 4：I/O 层统一

目标：把 `.nc` 和 `.tif` 读取逻辑统一为数组接口。

建议新增：

```text
eddy_identify/io/readers.py
```

目标接口：

```python
read_sla_uv(path) -> dict
```

返回：

```python
{
    "sla": sla,
    "u": u,
    "v": v,
    "lon": lon,
    "lat": lat,
    "metadata": metadata,
}
```

这一阶段先新增函数，不立刻替换旧流程。

## Phase 5：识别核心模块化

在结果完全一致后，再逐步抽取：

```text
eddy_identify/core/grid.py
eddy_identify/core/seeds.py
eddy_identify/core/contours.py
eddy_identify/core/diagnostics.py
eddy_identify/core/merge.py
```

每抽取一个模块，都要保证 baseline 统计完全一致或差异可解释。

## Phase 6：算法优化

只有在模块化完成后再做。

可选优化：

1. Gaussian 高通滤波与 Bessel 高通滤波对比；
2. shape error、振幅阈值、像素阈值的区域化或分辨率化；
3. 重叠区去重加入边界 IoU；
4. 输出 GeoJSON、NetCDF mask、Parquet 表格；
5. 与现代 `py-eddy-tracker` API 对齐。

## 3. 不建议立即做的事情

以下操作风险较高，不建议在没有基准测试前做：

- 直接删除旧文件；
- 直接移动 `make_eddy_track_AVISO_nc.py`；
- 直接升级 NumPy 到 2.x；
- 直接把 PyQt4 改成 PyQt5；
- 直接将 Basemap 改成 Cartopy；
- 直接修改 shape error、振幅阈值、滤波核大小；
- 直接改变输出 JSON 字段名。

## 4. 建议的每次 PR 模板

每个 PR 应回答：

1. 本次修改了什么？
2. 是否修改算法？
3. 是否修改输出字段？
4. 是否影响历史结果？
5. 是否已和 baseline 比较？
6. 如果结果不同，原因是什么？

## 5. 当前状态

当前阶段：Step 1，文档和环境整理。

算法文件状态：未修改。
