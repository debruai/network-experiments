# 拥塞控制算法实验项目

> TCP Reno 与 CUBIC 算法对比实现  
> 适用课程：计算机网络、网络协议分析、网络性能评估  
> 最后更新：2026年5月

---

## 🚀 一键运行

```bash
cd "通信与网络/ 实验/congestion_control"
./run_demo.sh
```

或者手动激活虚拟环境：

```bash
cd "通信与网络/ 实验/congestion_control"
source venv/bin/activate
python examples/basic_demo.py
# 提示时输入 n 回车
```

## 快速复现指南

### 环境准备

本项目有独立的Python虚拟环境，所有依赖已装在其中。

**❗ 必须先激活虚拟环境再运行，否则报 No module named 'numpy'**

```bash
# 进入项目目录
cd "通信与网络/ 实验/congestion_control"

# ⭐ 第一步：激活虚拟环境（必须！）
source venv/bin/activate

# 验证是否激活成功（出现 (venv) 前缀即为成功）
which python
```

### 运行演示

```bash
# 确保已激活虚拟环境（最前面有 (venv) 标记）
source venv/bin/deactivate   # 如果之前激活了其他环境
cd "通信与网络/ 实验/congestion_control"
source venv/bin/activate

# 运行基础演示
python examples/basic_demo.py

# 提示"是否运行网络模拟演示？(y/n): " 时输入 n 回车
# （输入 y 会跑较长时间的模拟）
```

### 查看结果

```bash
ls -la demo_output/
cat demo_output/algorithm_comparison.txt
```

### 运行测试

```bash
python -m pytest tests/ -v
```

---

## 📁 项目结构

```
congestion_control/
├── src/                        源代码
│   ├── algorithms/            拥塞控制算法
│   │   ├── base.py           算法基类
│   │   ├── reno.py           TCP Reno实现
│   │   ├── cubic.py          CUBIC实现
│   │   └── factory.py        算法工厂
│   ├── network/              网络模拟
│   │   ├── channel.py        网络信道模型
│   │   └── simulator.py      网络模拟器
│   ├── metrics/              性能指标
│   │   └── collector.py      指标收集器
│   └── visualization/        可视化
│       └── plotter.py        图表绘制工具
├── examples/                  使用示例
│   ├── basic_demo.py         基础演示
│   ├── advanced_demo.py      高级演示
│   └── comprehensive_demo.py 完整对比
├── tests/                     单元测试
├── demo_output/               运行结果输出
│   ├── cwnd_comparison.png   拥塞窗口对比图
│   ├── throughput_comparison.png 吞吐量对比图
│   └── algorithm_comparison.txt  数据对比
├── reports/                   报告模板
├── requirements.txt           依赖
├── run_demo.sh                一键运行脚本
└── README.md                  本文件
```

---

## 🧠 核心功能

### 算法实现

**TCP Reno**
- 慢启动 (Slow Start)
- 拥塞避免 (Congestion Avoidance)
- 快速重传 (Fast Retransmit)
- 快速恢复 (Fast Recovery)

**CUBIC**
- 立方增长函数
- RTT公平性优化
- TCP友好模式
- 快速收敛机制

### 网络模拟

```python
from src.network.simulator import NetworkSimulator

simulator = NetworkSimulator(
    algorithm_type="reno",
    bandwidth=10.0,        # Mbps
    delay=50.0,            # ms
    loss_probability=0.05, # 5%丢包率
    simulation_duration=30.0
)
metrics = simulator.run()
print(f"吞吐量: {metrics.throughput_mbps:.2f} Mbps")
```

---

## 📊 算法对比结果

| 测试场景 | 算法 | 吞吐量(Mbps) | 平均cwnd |
|---------|------|-------------|----------|
| 稳定网络 | TCP Reno | 8.2 | 12.5 |
| 稳定网络 | CUBIC | 9.1 | 15.3 |
| 高延迟网络 | TCP Reno | 7.8 | 10.2 |
| 高延迟网络 | CUBIC | 8.5 | 13.8 |
| 高丢包网络 | TCP Reno | 6.5 | 8.5 |
| 高丢包网络 | CUBIC | 7.2 | 10.2 |

### 关键发现

1. **TCP Reno**: 采用AIMD策略，响应迅速但波动较大，适合传统网络
2. **CUBIC**: 采用立方增长函数，更平滑，适合高速网络
3. CUBIC在高带宽延迟积网络中表现更优
4. CUBIC具有更好的RTT公平性

---

## 📚 参考文献

1. RFC 5681 - TCP Congestion Control
2. Ha, S., et al. "CUBIC: A New TCP-Friendly High-Speed TCP Variant"
3. Kurose, J. F., & Ross, K. W. "Computer Networking: A Top-Down Approach"
4. Stevens, W. R. "TCP/IP Illustrated, Volume 1"
