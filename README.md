# eddy_identify

基于等值线法的海洋中尺度涡识别与结果输出代码。

> 当前仓库包含较早期的 `py-eddy-tracker` 思路代码、AVISO/Copernicus SLA 数据读取、全球分块识别、重叠区合并、绘图和 mask 输出等功能。第一阶段整理只补充文档和环境说明，不修改任何识别算法。

## 1. 项目定位

本项目主要用于从海表高度异常或海表高度场中识别中尺度涡，并输出涡旋属性、边界、涡心、mask 和可视化结果。代码当前更接近研究和生产脚本集合，而不是已经完全模块化的软件包。

适合的用途包括：

- AVISO/Copernicus 0.25° SLA 数据的批量涡旋识别；
- 全球或重点海区的涡旋目录生成；
- 深度学习涡旋识别任务的标签生产；
- 涡旋半径、振幅、EKE、相对涡度、散度和形变率等属性提取。

## 2. 当前核心文件

| 文件 | 主要作用 |
|---|---|
| `make_eddy_track_AVISO_nc.py` | 当前主要核心程序，读取 `.nc` 格式 SLA、`ugosa`、`vgosa`，进行分块识别和结果合并。 |
| `make_eddy_track_AVISO.py` | 较早期 `.tif` 输入版本，逻辑与 nc 版本高度相似。 |
| `py_eddy_tracker_classes.py` | 包含局地极值、圆拟合、shape error、等值线筛选、平均地转流速度等函数。 |
| `make_eddy_tracker_list_obj.py` | 涡旋对象、边界框、距离和等值线重采样等辅助对象。 |
| `NeighborsSearch.py` | 使用 KDTree 查找相邻分块，用于重叠区域合并。 |
| `haversine_distmat_py.py` | 球面距离计算工具。 |

## 3. 当前识别流程

```text
输入 SLA / ugosa / vgosa
  ↓
经度 0/360° 周期边界扩展
  ↓
高通滤波：SLA - Gaussian low-pass(SLA)
  ↓
按经纬度分块，并设置重叠区
  ↓
寻找 SLA 局地极大值和极小值作为反气旋/气旋种子点
  ↓
生成 SLA 闭合等值线
  ↓
筛选只包含一个种子点的闭合等值线
  ↓
计算边界内像素数、振幅、半径、shape error、平均速度等
  ↓
确定有效边界、最大平均速度边界、最内层边界
  ↓
合并所有分块结果，去除重叠区重复涡旋
  ↓
输出 JSON、图像和可选 mask
```

## 4. 与 py-eddy-tracker 官方示例的关系

本项目保留了早期 `py-eddy-tracker 1.4.1` 的代码结构和思想，但已经加入了较多本地化改造：

- 增加 AVISO/Copernicus `.nc` 和历史 `.tif` 两套读取流程；
- 直接读取 `ugosa`、`vgosa`，而不是全部从 ADT/SLA 重新计算地转流；
- 增加全球分块、重叠区合并和 0/360° 经度边界处理；
- 输出更丰富的诊断量，包括 EKE、相对涡度、散度、剪切形变率、拉伸形变率等；
- 输出自定义 JSON、可视化图和 mask，便于后续 AI 标签生产。

官方示例参考：

- https://py-eddy-tracker.readthedocs.io/en/stable/python_module/02_eddy_identification/pet_eddy_detection.html

## 5. 当前主要风险

在修改算法前，需要注意以下风险：

1. 代码中存在大量历史路径、硬编码参数和调试语句；
2. `.tif` 与 `.nc` 两套流程重复度高，后续需要统一 I/O；
3. 旧依赖包括 `PyQt4`、`Basemap`、`GDAL`，现代环境中安装难度较高；
4. 代码使用了 `np.float`、`np.int` 等旧写法，建议在重构前固定 NumPy 版本；
5. 分块合并目前主要基于涡心距离和振幅大小，后续可增加边界重叠率、半径相似度和极性一致性判断；
6. 当前阶段不应直接大规模移动函数，否则容易破坏隐式调用关系。

## 6. 建议的谨慎重构顺序

### Step 1：文档和环境整理

不改任何算法文件，只新增：

- `README.md`
- `environment.yml`
- `docs/REFACTOR_PLAN.md`
- `docs/BASELINE_CHECKLIST.md`

### Step 2：建立基准测试

选择固定日期和固定区域，保存当前版本结果，作为后续所有修改的对照。

### Step 3：路径和参数配置化

将硬编码路径和参数逐步移动到配置文件中，但不改变默认值。

### Step 4：统一 nc/tif 读取层

将数据读取从识别函数中剥离，使核心算法只接收 `sla`、`u`、`v`、`lon`、`lat` 数组。

### Step 5：模块化核心算法

逐步拆分：

- grid 构建；
- seed 检测；
- contour 筛选；
- 诊断量计算；
- 分块合并；
- 输出。

### Step 6：与官方 py-eddy-tracker 对比验证

用同一天、同一区域数据，对比涡旋数量、涡心位置、半径、振幅、边界重叠率和漏检误检案例。

## 7. 当前阶段运行建议

在完全重构前，不建议直接升级到最新 NumPy / SciPy / Matplotlib。建议优先使用 legacy 环境，并先验证核心脚本能否复现历史结果。

如果只做命令行识别，优先从 `make_eddy_track_AVISO_nc.py` 中的 `gloabal_eddy_multi_detect()` 开始；如果使用 GUI，需要额外解决 `PyQt4` 兼容问题。
