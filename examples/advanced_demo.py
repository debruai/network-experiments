"""
拥塞控制算法高级演示
自动运行完整的演示，不需要用户交互
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.algorithms.factory import AlgorithmFactory
from src.metrics.collector import MetricsCollector, MetricType
from src.visualization.plotter import MetricsPlotter, PlotConfig


def main():
    print("拥塞控制算法高级演示")
    print("=" * 50)
    
    # 1. 创建算法实例
    print("\n1. 创建算法实例...")
    reno = AlgorithmFactory.create_algorithm("reno", initial_cwnd=2)
    cubic = AlgorithmFactory.create_algorithm("cubic", beta=0.7, C=0.4)
    
    print(f"TCP Reno: {reno}")
    print(f"CUBIC: {cubic}")
    
    # 2. 模拟网络传输
    print("\n2. 模拟网络传输...")
    print("模拟100个ACK事件...")
    
    reno_cwnd_history = []
    cubic_cwnd_history = []
    
    # 模拟不同的网络条件
    for i in range(1, 101):
        # 随机RTT变化
        rtt = 50.0 + np.random.normal(0, 10)
        
        # 随机丢包
        if np.random.random() < 0.05:  # 5%丢包率
            # 模拟三个重复ACK
            for _ in range(3):
                reno.on_ack(i, rtt_sample=rtt)
                cubic.on_ack(i, rtt_sample=rtt)
            # 触发丢包
            reno.on_loss("triple_duplicate")
            cubic.on_loss("triple_duplicate")
        else:
            reno.on_ack(i, rtt_sample=rtt)
            cubic.on_ack(i, rtt_sample=rtt)
        
        reno_cwnd_history.append(reno.cwnd)
        cubic_cwnd_history.append(cubic.cwnd)
        
        if i % 20 == 0:
            print(f"  ACK {i}: Reno cwnd={reno.cwnd:.2f}, CUBIC cwnd={cubic.cwnd:.2f}")
    
    # 3. 收集性能指标
    print("\n3. 收集性能指标...")
    collector = MetricsCollector()
    
    # 模拟吞吐量数据
    for i in range(100):
        # TCP Reno吞吐量
        reno_throughput = reno_cwnd_history[i] * 1460 * 8 / (rtt / 1000) / 1e6  # Mbps
        cubic_throughput = cubic_cwnd_history[i] * 1460 * 8 / (rtt / 1000) / 1e6  # Mbps
        
        collector.record(reno_throughput, MetricType.THROUGHPUT, "TCP Reno")
        collector.record(cubic_throughput, MetricType.THROUGHPUT, "CUBIC")
        collector.record(reno_cwnd_history[i], MetricType.CWND, "TCP Reno")
        collector.record(cubic_cwnd_history[i], MetricType.CWND, "CUBIC")
        collector.record(rtt, MetricType.RTT, "TCP Reno")
        collector.record(rtt, MetricType.RTT, "CUBIC")
    
    print(f"收集了 {collector.get_total_samples()} 个指标样本")
    
    # 4. 分析算法性能
    print("\n4. 算法性能分析...")
    
    algorithms = ["TCP Reno", "CUBIC"]
    metrics = [MetricType.THROUGHPUT, MetricType.CWND, MetricType.RTT]
    
    for algo in algorithms:
        print(f"\n{algo} 性能统计:")
        for metric in metrics:
            stats = collector.get_statistics(algo, metric)
            if stats:
                print(f"  {metric.value}: 均值={stats['mean']:.2f}, 标准差={stats['std']:.2f}")
    
    # 5. 算法比较
    print("\n5. 算法比较...")
    comparison = collector.compare_algorithms("TCP Reno", "CUBIC")
    
    # 从比较结果中提取统计信息
    comparisons = comparison.metrics
    
    # 统计哪个算法表现更好
    reno_better = 0
    cubic_better = 0
    tie = 0
    
    for metric_data in comparisons.values():
        better_algo = metric_data.get("better_algorithm", "")
        if better_algo == "TCP Reno":
            reno_better += 1
        elif better_algo == "CUBIC":
            cubic_better += 1
        else:
            tie += 1
    
    print(f"比较指标数: {len(comparisons)}")
    print(f"TCP Reno 表现更好的指标数: {reno_better}")
    print(f"CUBIC 表现更好的指标数: {cubic_better}")
    print(f"平局指标数: {tie}")
    
    # 6. 生成可视化图表
    print("\n6. 生成可视化图表...")
    
    # 确保输出目录存在
    output_dir = "demo_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    plotter = MetricsPlotter(collector)
    
    # 生成拥塞窗口对比图
    print("  生成拥塞窗口对比图...")
    plotter.plot_cwnd_comparison(
        algorithms,
        PlotConfig(
            title="拥塞窗口对比 (高级演示)",
            save_path=os.path.join(output_dir, "advanced_cwnd_comparison.png"),
            figsize=(12, 6)
        )
    )
    
    # 生成吞吐量对比图
    print("  生成吞吐量对比图...")
    plotter.plot_throughput_comparison(
        algorithms,
        PlotConfig(
            title="吞吐量对比 (高级演示)",
            save_path=os.path.join(output_dir, "advanced_throughput_comparison.png"),
            figsize=(12, 6)
        )
    )
    
    # 生成RTT对比图
    print("  生成RTT对比图...")
    plotter.plot_rtt_comparison(
        algorithms,
        PlotConfig(
            title="RTT对比 (高级演示)",
            save_path=os.path.join(output_dir, "advanced_rtt_comparison.png"),
            figsize=(12, 6)
        )
    )
    
    # 7. 保存比较结果
    print("\n7. 保存比较结果...")
    comparison_path = os.path.join(output_dir, "advanced_algorithm_comparison.txt")
    with open(comparison_path, "w", encoding="utf-8") as f:
        f.write("拥塞控制算法高级比较结果\n")
        f.write("=" * 50 + "\n\n")
        f.write(comparison.summary)
        
        f.write("\n详细比较:\n")
        for metric_name, comp in comparisons.items():
            f.write(f"\n{metric_name}:\n")
            f.write(f"  TCP Reno: {comp['TCP Reno']:.4f}\n")
            f.write(f"  CUBIC: {comp['CUBIC']:.4f}\n")
            f.write(f"  差异: {comp['difference']:.4f} ({comp['difference_percent']:.1f}%)\n")
            f.write(f"  更好的算法: {comp['better_algorithm']}\n")
    
    print(f"比较结果已保存到: {comparison_path}")
    
    # 8. 网络模拟演示
    print("\n8. 网络模拟演示...")
    try:
        from src.network.simulator import NetworkSimulator
        
        print("  运行TCP Reno网络模拟...")
        reno_simulator = NetworkSimulator(
            algorithm_type="reno",
            bandwidth=10.0,
            delay=50.0,
            loss_probability=0.05,
            simulation_duration=10.0
        )
        reno_metrics = reno_simulator.run()
        
        print("  运行CUBIC网络模拟...")
        cubic_simulator = NetworkSimulator(
            algorithm_type="cubic",
            bandwidth=10.0,
            delay=50.0,
            loss_probability=0.05,
            simulation_duration=10.0
        )
        cubic_metrics = cubic_simulator.run()
        
        print("\n网络模拟结果:")
        print(f"  TCP Reno: 吞吐量={reno_metrics.throughput_mbps:.2f} Mbps, 丢包率={reno_metrics.loss_rate:.2%}")
        print(f"  CUBIC: 吞吐量={cubic_metrics.throughput_mbps:.2f} Mbps, 丢包率={cubic_metrics.loss_rate:.2%}")
        
    except ImportError as e:
        print(f"  网络模拟模块导入失败: {e}")
    except Exception as e:
        print(f"  网络模拟运行失败: {e}")
    
    # 9. 总结
    print("\n" + "=" * 50)
    print("演示完成!")
    print(f"生成的图表保存在: {output_dir}/")
    print(f"比较结果保存在: {comparison_path}")
    
    # 显示关键发现
    print("\n关键发现:")
    if reno_better > cubic_better:
        print("  - 在当前测试条件下，TCP Reno表现更好")
    elif cubic_better > reno_better:
        print("  - 在当前测试条件下，CUBIC表现更好")
    else:
        print("  - 在当前测试条件下，两种算法表现相当")
    
    print("  - 详细比较结果请查看保存的文件")
    print("\n演示程序结束。")


if __name__ == "__main__":
    main()
