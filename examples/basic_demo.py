"""
拥塞控制算法基础演示
展示TCP Reno和CUBIC算法的基本使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms.factory import AlgorithmFactory
from src.metrics.collector import MetricsCollector, MetricType
from src.visualization.plotter import MetricsPlotter, PlotConfig
import time
import numpy as np


def demo_basic_algorithm_behavior():
    """演示算法基本行为"""
    print("=== 拥塞控制算法基础演示 ===\n")
    
    # 1. 创建算法实例
    print("1. 创建算法实例:")
    reno = AlgorithmFactory.create_algorithm("reno", initial_cwnd=2)
    cubic = AlgorithmFactory.create_algorithm("cubic", beta=0.7, C=0.4)
    
    print(f"TCP Reno: {reno}")
    print(f"CUBIC: {cubic}")
    print()
    
    # 2. 模拟ACK接收（慢启动阶段）
    print("2. 模拟慢启动阶段:")
    print("接收ACK 1-5 (RTT=50ms):")
    
    for i in range(1, 6):
        reno.on_ack(i, rtt_sample=50.0)
        cubic.on_ack(i, rtt_sample=50.0)
        
        print(f"  ACK {i}: Reno cwnd={reno.cwnd:.2f}, CUBIC cwnd={cubic.cwnd:.2f}")
    
    print()
    
    # 3. 设置慢启动阈值，进入拥塞避免
    print("3. 进入拥塞避免阶段:")
    reno.ssthresh = 5.0
    cubic.ssthresh = 5.0
    
    print("接收ACK 6-10:")
    for i in range(6, 11):
        reno.on_ack(i, rtt_sample=50.0)
        cubic.on_ack(i, rtt_sample=50.0)
        
        print(f"  ACK {i}: Reno cwnd={reno.cwnd:.2f}, CUBIC cwnd={cubic.cwnd:.2f}")
    
    print()
    
    # 4. 模拟丢包（三个重复ACK）
    print("4. 模拟丢包（三个重复ACK）:")
    print("发送三个重复ACK 10:")
    
    for _ in range(3):
        reno.on_ack(10, rtt_sample=50.0)  # 重复ACK
        cubic.on_ack(10, rtt_sample=50.0)
    
    print(f"丢包后: Reno cwnd={reno.cwnd:.2f}, CUBIC cwnd={cubic.cwnd:.2f}")
    print(f"Reno状态: {reno.state}, CUBIC状态: {cubic.state}")
    
    # 5. 获取算法参数
    print("\n5. 算法参数:")
    print(f"TCP Reno参数: cwnd={reno.cwnd:.2f}, ssthresh={reno.ssthresh:.2f}, state={reno.state}")
    
    if hasattr(cubic, 'get_parameters'):
        cubic_params = cubic.get_parameters()
        print(f"CUBIC参数: {cubic_params}")
    
    return reno, cubic


def demo_metrics_collection():
    """演示指标收集"""
    print("\n=== 性能指标收集演示 ===\n")
    
    collector = MetricsCollector()
    
    # 模拟算法运行并收集指标
    algorithms = ["TCP Reno", "CUBIC"]
    
    for algo_name in algorithms:
        if algo_name == "TCP Reno":
            algo = AlgorithmFactory.create_algorithm("reno")
        else:
            algo = AlgorithmFactory.create_algorithm("cubic")
        
        print(f"运行{algo_name}并收集指标...")
        
        # 模拟网络传输
        for i in range(1, 51):
            # 模拟RTT变化
            rtt = 50.0 + np.random.normal(0, 5)
            
            # 接收ACK
            algo.on_ack(i, rtt_sample=rtt)
            
            # 收集指标
            collector.record(algo.cwnd, MetricType.CWND, algo_name, {"iteration": i})
            collector.record(rtt, MetricType.RTT, algo_name, {"iteration": i})
            
            # 模拟吞吐量（简化计算）
            throughput = algo.cwnd * 1460 * 8 / (rtt / 1000) / 1_000_000  # Mbps
            collector.record(throughput, MetricType.THROUGHPUT, algo_name, {"iteration": i})
            
            # 每10个ACK模拟一次丢包
            if i % 10 == 0:
                algo.on_loss("triple_duplicate")
                collector.record(0.1, MetricType.LOSS_RATE, algo_name, {"iteration": i})
    
    print(f"收集了 {len(collector.samples)} 个指标样本")
    
    # 显示统计信息
    print("\n算法统计信息:")
    for algo in algorithms:
        print(f"\n{algo}:")
        
        cwnd_stats = collector.get_statistics(algo, MetricType.CWND)
        print(f"  拥塞窗口: 均值={cwnd_stats['mean']:.2f}, 标准差={cwnd_stats['std']:.2f}")
        
        throughput_stats = collector.get_statistics(algo, MetricType.THROUGHPUT)
        print(f"  吞吐量: 均值={throughput_stats['mean']:.2f} Mbps")
        
        rtt_stats = collector.get_statistics(algo, MetricType.RTT)
        print(f"  RTT: 均值={rtt_stats['mean']:.1f} ms")
    
    return collector


def demo_visualization(collector):
    """演示数据可视化"""
    print("\n=== 数据可视化演示 ===\n")
    
    plotter = MetricsPlotter(collector)
    algorithms = ["TCP Reno", "CUBIC"]
    
    # 创建输出目录
    output_dir = "demo_output"
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("生成可视化图表...")
    
    # 1. 拥塞窗口图
    print("1. 生成拥塞窗口比较图...")
    plotter.plot_cwnd_comparison(algorithms, PlotConfig(
        title="拥塞窗口随时间变化",
        save_path=os.path.join(output_dir, "cwnd_comparison.png"),
        show=False
    ))
    
    # 2. 吞吐量图
    print("2. 生成吞吐量比较图...")
    plotter.plot_throughput_comparison(algorithms, PlotConfig(
        title="吞吐量随时间变化",
        save_path=os.path.join(output_dir, "throughput_comparison.png"),
        show=False
    ))
    
    # 3. 算法比较
    print("3. 生成算法性能比较...")
    comparison = collector.compare_algorithms("TCP Reno", "CUBIC")
    print(comparison.summary)
    
    # 保存比较结果到文件
    comparison_file = os.path.join(output_dir, "algorithm_comparison.txt")
    with open(comparison_file, 'w') as f:
        f.write(comparison.summary)
    
    print(f"\n图表已保存到 '{output_dir}' 目录")
    print(f"比较结果已保存到 '{comparison_file}'")
    
    return output_dir


def demo_network_simulation():
    """演示网络模拟"""
    print("\n=== 网络模拟演示 ===\n")
    
    from src.network.simulator import NetworkSimulator
    
    # 测试不同网络条件下的算法性能
    test_cases = [
        {
            "name": "稳定网络",
            "bandwidth": 10.0,
            "delay": 50.0,
            "loss_probability": 0.0
        },
        {
            "name": "高延迟网络",
            "bandwidth": 10.0,
            "delay": 200.0,
            "loss_probability": 0.0
        },
        {
            "name": "高丢包网络",
            "bandwidth": 10.0,
            "delay": 50.0,
            "loss_probability": 0.1
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"  带宽: {test_case['bandwidth']} Mbps")
        print(f"  延迟: {test_case['delay']} ms")
        print(f"  丢包率: {test_case['loss_probability']:.1%}")
        
        # 测试TCP Reno
        print("  运行TCP Reno...")
        reno_simulator = NetworkSimulator(
            algorithm_type="reno",
            bandwidth=test_case['bandwidth'],
            delay=test_case['delay'],
            loss_probability=test_case['loss_probability'],
            simulation_duration=5.0  # 缩短模拟时间以加快演示
        )
        reno_metrics = reno_simulator.run()
        
        # 测试CUBIC
        print("  运行CUBIC...")
        cubic_simulator = NetworkSimulator(
            algorithm_type="cubic",
            bandwidth=test_case['bandwidth'],
            delay=test_case['delay'],
            loss_probability=test_case['loss_probability'],
            simulation_duration=5.0
        )
        cubic_metrics = cubic_simulator.run()
        
        results[test_case['name']] = {
            "TCP Reno": reno_metrics,
            "CUBIC": cubic_metrics
        }
    
    # 显示结果比较
    print("\n=== 网络模拟结果比较 ===")
    print("\n" + "="*70)
    print(f"{'测试场景':<15} {'算法':<10} {'吞吐量(Mbps)':<15} {'丢包率':<10} {'平均cwnd':<10}")
    print("="*70)
    
    for test_name, algo_results in results.items():
        for algo_name, metrics in algo_results.items():
            print(f"{test_name:<15} {algo_name:<10} {metrics.throughput_mbps:<15.2f} "
                  f"{metrics.loss_rate:<10.2%} {metrics.avg_cwnd:<10.2f}")
    
    return results


def main():
    """主函数"""
    print("拥塞控制算法演示程序")
    print("=" * 50)
    
    try:
        # 演示1: 算法基本行为
        reno, cubic = demo_basic_algorithm_behavior()
        
        # 演示2: 指标收集
        collector = demo_metrics_collection()
        
        # 演示3: 数据可视化
        output_dir = demo_visualization(collector)
        
        # 演示4: 网络模拟（可选，时间较长）
        run_simulation = input("\n是否运行网络模拟演示？(y/n): ").lower().strip()
        if run_simulation == 'y':
            results = demo_network_simulation()
        
        print("\n" + "="*50)
        print("演示完成!")
        print(f"所有输出文件保存在: {os.path.abspath('demo_output')}")
        
        # 显示关键发现
        print("\n关键发现:")
        print("1. TCP Reno采用AIMD策略，在丢包时窗口减半")
        print("2. CUBIC采用立方增长函数，更适合高速网络")
        print("3. 在高延迟或高丢包网络中，算法表现差异明显")
        print("4. 可视化工具帮助直观比较算法性能")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
