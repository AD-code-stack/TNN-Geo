# IP地理定位: Traceroute位置传播与IP范围插值

这是论文 "IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation" (WWW 2021) 的Python实现。

## 概述

本项目实现了一种新颖的IP地理定位技术,结合了两个关键方法:

1. **Traceroute位置传播**: 通过利用网络跳点之间的延迟关系,沿着traceroute路径传播IP位置信息
2. **IP范围位置插值**: 基于已知IP推断整个IP范围的位置,扩展覆盖范围

该方法相比商业地理定位数据库的准确率提高了31个百分点。

## 核心特性

- ✅ **延迟邻居提取**: 识别网络延迟相似的IP对
- ✅ **邻居对聚合**: 聚合同一IP对在多条traceroute中的出现
- ✅ **IP范围插值**: 使用/24网段扩展ground truth覆盖范围
- ✅ **迭代位置传播**: 通过网络图传播位置信息
- ✅ **灵活配置**: 支持高准确性和高覆盖率两种模式

## 项目结构

```
.
├── src/
│   ├── data_processing/           # 数据加载和解析
│   │   ├── traceroute_parser.py   # 解析traceroute数据
│   │   └── ground_truth_loader.py # 加载真实位置数据
│   ├── latency_neighbors/         # 延迟邻居提取
│   │   └── neighbor_extractor.py  # 提取和聚合邻居对
│   ├── ip_range_interpolation/    # IP范围插值
│   │   └── range_interpolator.py  # 为IP范围插值位置
│   ├── location_propagation/      # 位置传播
│   │   └── propagator.py          # 通过网络传播位置
│   └── utils/
│       ├── config_loader.py       # 加载配置
│       └── geo_utils.py           # 地理工具函数
├── config/
│   └── config.yaml                # 配置文件
├── data/
│   ├── ground_truth/              # 真实IP位置
│   ├── traceroute/                # Traceroute数据
│   └── output/                    # 输出结果
├── main.py                        # 主程序入口
└── README_CN.md                   # 中文文档
```

## 安装

### 环境要求
- Python 3.7+
- pip

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/IP-Geo.git
cd IP-Geo

# 安装依赖
pip install numpy pandas pyyaml scikit-learn
```

## 使用方法

### 1. 准备数据

将数据放在以下目录结构中:

```
data/
├── ground_truth/
│   └── ground_truth.csv          # 格式: ip,latitude,longitude
└── traceroute/
    └── traceroute_sample.txt     # 格式: source_ip dest_ip hop1 rtt1 hop2 rtt2 ...
```

### 2. 配置参数

编辑 `config/config.yaml` 调整参数:

```yaml
latency_neighbors:
  high_accuracy:
    max_latency_diff: 2    # X: 最大延迟差(毫秒)
    max_rtt: 2             # Y: 最大RTT(毫秒)
  high_coverage:
    max_latency_diff: 3
    max_rtt: 9

ip_range_interpolation:
  range_size: 256          # /24网段
  min_ground_truth: 2      # n: 每个范围最少已知IP数
  max_distance_km: 25      # m: 范围内最大距离(公里)

location_propagation:
  mode: "high_accuracy"    # 或 "high_coverage"
  max_iterations: 10
  convergence_threshold: 0.01
```

### 3. 运行管道

```bash
python main.py
```

### 输出结果

结果保存到 `data/output/`:

- `latency_neighbors_high_accuracy.csv`: 提取的邻居对(高准确性)
- `latency_neighbors_high_coverage.csv`: 提取的邻居对(高覆盖率)
- `ip_ranges.csv`: 有效的IP范围及中心坐标
- `interpolated_ips.csv`: 插值后的IP位置
- `propagated_ips.csv`: 传播得到的IP位置
- `all_locations.csv`: 完整结果(插值+传播)

## 方法详解

### 第1步: 延迟邻居提取

识别网络延迟接近的IP对:

```
条件: |RTT(ip1) - RTT(ip2)| ≤ X ms 且 RTT(ip1), RTT(ip2) ≤ Y ms
```

**两阶段聚合**:
1. 聚合每个(source_ip, hop_ip)对在多条traceroute中的RTT
2. 聚合同一IP对在多条traceroute中的延迟差

### 第2步: IP范围插值

通过为整个/24网段分配位置来扩展覆盖范围:

```
对于每个/24范围:
  如果 (已知IP数 ≥ n) 且 (所有IP距离 ≤ m km):
    则 将质心位置分配给整个范围
```

**参数**:
- n = 2 (最少已知IP数)
- m = 25 km (最大距离)

**效果**: 将覆盖范围从890万扩展到3.82亿个IP

### 第3步: 位置传播

通过网络图迭代传播位置:

```
第1次迭代: 传播到距已知IP 1跳的IP
第2次迭代: 传播到距已知IP 2跳的IP
...
直到收敛或达到最大迭代次数
```

**位置计算**: 邻居位置的平均值

## 配置模式

### 高准确性模式
- 参数: X=2ms, Y=2ms
- 中位误差: ~4.3 km
- 准确率(<10km): ~67.7%
- 适用场景: 欺诈检测、内容版权限制

### 高覆盖率模式
- 参数: X=3ms, Y=9ms
- 中位误差: ~10.1 km
- 准确率(<10km): ~50.5%
- 适用场景: 广告投放、内容个性化

## 论文信息

**标题**: IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation

**作者**: Ovidiu Dan, Vaibhav Parikh, Brian D. Davison

**会议**: WWW 2021 (The Web Conference 2021)

**DOI**: 10.1145/3442442.3451888

**链接**: https://dl.acm.org/doi/10.1145/3442442.3451888

## 关键结果

| 指标 | 高准确性 | 高覆盖率 | 商业DB A | 商业DB B |
|------|---------|---------|---------|---------|
| 中位误差 | 4.3 km | 10.1 km | 11.1 km | 16.7 km |
| <10km准确率 | 67.7% | 50.5% | 47.2% | 36.7% |
| <20km准确率 | 99.4% | 98.3% | - | - |

## 实现说明

### 数据格式

**Ground Truth CSV**:
```csv
ip,latitude,longitude
8.8.8.8,37.386,-122.084
1.1.1.1,37.751,-97.822
```

**Traceroute TXT**:
```
source_ip dest_ip hop1 rtt1 hop2 rtt2 hop3 rtt3 ...
100.38.192.94 129.11.202.144 107.15.57.240 2.04 22.55.246.62 3.40 ...
```

### 核心算法

1. **Haversine距离**: 计算两点间的大圆距离
2. **质心计算**: 计算多个位置的中心点
3. **迭代传播**: 基于图的位置传播,带收敛检测

## 依赖库

- numpy: 数值计算
- pandas: 数据处理
- pyyaml: 配置解析
- scikit-learn: 机器学习工具

## 限制条件

- 需要充足的ground truth数据以获得准确的插值
- 依赖traceroute数据的质量和覆盖范围
- 网络拓扑变化可能影响准确性
- 需要考虑位置数据的隐私问题

## 未来改进

- 支持IPv6地址
- 集成反向DNS信息
- 基于机器学习的位置优化
- 实时位置更新

## 许可证

本项目仅供研究和教育用途。

## 引用

如果在研究中使用本实现,请引用原论文:

```bibtex
@inproceedings{dan2021ip,
  title={IP Geolocation Using Traceroute Location Propagation and IP Range Location Interpolation},
  author={Dan, Ovidiu and Parikh, Vaibhav and Davison, Brian D},
  booktitle={Companion Proceedings of the Web Conference 2021},
  pages={332--338},
  year={2021},
  organization={ACM}
}
```

## 联系方式

如有问题或建议,欢迎提交Issue。

---

**最后更新**: 2026-03-11
