"""
拥塞控制算法综合演示
展示TCP Reno和CUBIC算法的完整功能对比
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt

# 配置中文字体
try:
    from src.visualization.font_config import configure_chinese_fonts
    configure_chinese_fonts()
except ImportError:
    # 如果字体配置不可用，使用简单配置
    try:
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass

from src.algorithms.factory import AlgorithmFactory
from src.network.simulator import NetworkSimulator
from src.metrics.collector import MetricsCollector, MetricType
from src.visualization.plotter import MetricsPlotter, PlotConfig


def demo_basic_algorithm_comparison():
    """演示基本算法对比"""
    print("=" * 60)
    print("拥塞控制算法基本对比演示")
    print("=" * 60)
    
    # 创建算法实例
    reno = AlgorithmFactory.create_algorithm("reno", initial_cwnd=1)
    cubic = AlgorithmFactory.create_algorithm("cubic", initial_cwnd=1, beta=0.7, C=0.4)
    
    algorithms = {
        "TCP Reno": reno,
        "CUBIC": cubic
    }
    
    # 模拟网络传输
    print("\n1. 模拟稳定网络传输 (RTT=50ms, 无丢包)")
    print("-" * 40)
    
    # 记录窗口历史
    cwnd_history = {name: [] for name in algorithms}
    time_points = []
    
    # 模拟100个ACK
    for i in range(1, 101):
        rtt = 50.0 + np.random.normal(0, 2)  # 轻微波动
        
        for name, algo in algorithms.items():
            algo.on_ack(i, rtt_sample=rtt)
            cwnd_history[name].append(algo.cwnd)
        
        time_points.append(i)
        
        # 每20个ACK打印一次状态
        if i % 20 == 0:
            print(f"ACK {i:3d}: ", end="")
            for name, algo in algorithms.items():
                print(f"{name}: cwnd={algo.cwnd:6.2f}  ", end="")
            print()
    
    # 绘制窗口对比图
    plt.figure(figsize=(12, 6))
    
    for name, history in cwnd_history.items():
        plt.plot(time_points, history, label=name, linewidth=2)
    
    plt.xlabel("ACK序号", fontsize=12)
    plt.ylabel("拥塞窗口 (cwnd)", fontsize=12)
    plt.title("TCP Reno vs CUBIC: 拥塞窗口对比 (稳定网络)", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图表
    output_dir = "demo_output"
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/cwnd_comparison_stable.png", dpi=150)
    print(f"\n图表已保存到: {output_dir}/cwnd_comparison_stable.png")
    
    # 显示统计信息
    print("\n2. 性能统计")
    print("-" * 40)
    
    for name, history in cwnd_history.items():
        avg_cwnd = np.mean(history)
        std_cwnd = np.std(history)
        max_cwnd = np.max(history)
        min_cwnd = np.min(history)
        
        print(f"{name}:")
        print(f"  平均cwnd: {avg_cwnd:.2f}")
        print(f"  标准差: {std_cwnd:.2f}")
        print(f"  最大值: {max_cwnd:.2f}")
        print(f"  最小值: {min_cwnd:.2f}")
        print(f"  波动率: {(std_cwnd/avg_cwnd*100):.1f}%")
        print()


def demo_loss_scenarios():
    """演示丢包场景下的算法表现"""
    print("\n" + "=" * 60)
    print("丢包场景算法表现演示")
    print("=" * 60)
    
    # 创建算法实例
    reno = AlgorithmFactory.create_algorithm("reno", initial_cwnd=1)
    cubic = AlgorithmFactory.create_algorithm("cubic", initial_cwnd=1)
    
    algorithms = {
        "TCP Reno": reno,
        "CUBIC": cubic
    }
    
    # 模拟有丢包的传输
    print("\n1. 模拟丢包事件 (在第30、60、90个ACK处丢包)")
    print("-" * 40)
    
    loss_points = [30, 60, 90]
    cwnd_history = {name: [] for name in algorithms}
    
    for i in range(1, 101):
        rtt = 50.0
        
        for name, algo in algorithms.items():
            # 模拟丢包
            if i in loss_points:
                # 触发快速重传
                for _ in range(3):
                    algo.on_ack(i-1, rtt_sample=rtt)  # 重复ACK
                print(f"  {name}: 在第{i}个ACK处检测到丢包，触发快速重传")
                print(f"    丢包前cwnd={algo.cwnd:.2f}, 丢包后cwnd={algo.cwnd:.2f}")
            
            # 正常ACK
            algo.on_ack(i, rtt_sample=rtt)
            cwnd_history[name].append(algo.cwnd)
    
    # 绘制丢包场景下的窗口变化
    plt.figure(figsize=(12, 6))
    
    for name, history in cwnd_history.items():
        plt.plot(range(1, 101), history, label=name, linewidth=2)
    
    # 标记丢包点
    for loss_point in loss_points:
        plt.axvline(x=loss_point, color='red', linestyle='--', alpha=0.5, label='丢包点' if loss_point == loss_points[0] else "")
    
    plt.xlabel("ACK序号", fontsize=12)
    plt.ylabel("拥塞窗口 (cwnd)", fontsize=12)
    plt.title("丢包场景下的算法表现", fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图表
    output_dir = "demo_output"
    plt.savefig(f"{output_dir}/cwnd_comparison_loss.png", dpi=150)
    print(f"\n图表已保存到: {output_dir}/cwnd_comparison_loss.png")


def demo_network_simulation():
    """演示网络模拟器功能"""
    print("\n" + "=" * 60)
    print("网络模拟器演示")
    print("=" * 60)
    
    # 创建网络模拟器
    print("\n1. 创建网络模拟器")
    print("-" * 40)
    
    network_configs = [
        {
            "name": "稳定网络",
            "bandwidth": 10.0,      # Mbps
            "delay": 50.0,          # ms
            "loss_probability": 0.0, # 0%
            "simulation_duration": 30.0  # 秒
        },
        {
            "name": "高延迟网络",
            "bandwidth": 10.0,
            "delay": 200.0,
            "loss_probability": 0.0,
            "simulation_duration": 30.0
        },
        {
            "name": "高丢包网络",
            "bandwidth": 10.0,
            "delay": 50.0,
            "loss_probability": 0.05,  # 5%
            "simulation_duration": 30.0
        }
    ]
    
    algorithm_types = ["reno", "cubic"]
    
    # 收集所有指标
    collector = MetricsCollector()
    
    for config in network_configs:
        print(f"\n模拟 {config['name']}:")
        print(f"  带宽: {config['bandwidth']} Mbps")
        print(f"  延迟: {config['delay']} ms")
        print(f"  丢包率: {config['loss_probability']*100:.1f}%")
        
        for algo_type in algorithm_types:
            simulator = NetworkSimulator(
                algorithm_type=algo_type,
                bandwidth=config["bandwidth"],
                delay=config["delay"],
                loss_probability=config["loss_probability"],
                simulation_duration=config["simulation_duration"]
            )
            
            # 运行模拟
            metrics = simulator.run()
            
            # 记录指标
            algorithm_name = "TCP Reno" if algo_type == "reno" else "CUBIC"
            scenario_name = f"{algorithm_name} - {config['name']}"
            
            collector.record(metrics.throughput_mbps, MetricType.THROUGHPUT, scenario_name)
            collector.record(metrics.avg_rtt, MetricType.RTT, scenario_name)
            collector.record(metrics.loss_rate, MetricType.LOSS_RATE, scenario_name)
            collector.record(metrics.avg_cwnd, MetricType.CWND, scenario_name)
            
            print(f"  {algorithm_name}:")
            print(f"    吞吐量: {metrics.throughput_mbps:.2f} Mbps")
            print(f"    平均RTT: {metrics.avg_rtt:.1f} ms")
            print(f"    丢包率: {metrics.loss_rate:.2%}")
            print(f"    平均cwnd: {metrics.avg_cwnd:.2f}")
    
    # 创建性能对比图表
    print("\n2. 生成性能对比图表")
    print("-" * 40)
    
    plotter = MetricsPlotter(collector)
    
    # 绘制吞吐量对比图
    plotter.plot_metric_comparison(
        metric_type=MetricType.THROUGHPUT,
        config=PlotConfig(
            title="不同网络场景下的吞吐量对比",
            ylabel="吞吐量 (Mbps)",
            save_path="demo_output/throughput_comparison.png"
        )
    )
    
    # 绘制RTT对比图
    plotter.plot_metric_comparison(
        metric_type=MetricType.RTT,
        config=PlotConfig(
            title="不同网络场景下的RTT对比",
            ylabel="RTT (ms)",
            save_path="demo_output/rtt_comparison.png"
        )
    )
    
    print("图表已保存到 demo_output/ 目录")


def demo_advanced_features():
    """演示高级功能"""
    print("\n" + "=" * 60)
    print("高级功能演示")
    print("=" * 60)
    
    print("\n1. 算法参数调优演示")
    print("-" * 40)
    
    # 测试不同CUBIC参数
    beta_values = [0.5, 0.7, 0.8]
    C_values = [0.3, 0.4, 0.5]
    
    results = []
    
    for beta in beta_values:
        for C in C_values:
            cubic = AlgorithmFactory.create_algorithm(
                "cubic",
                initial_cwnd=1,
                beta=beta,
                C=C
            )
            
            # 模拟传输
            for i in range(1, 51):
                cubic.on_ack(i, rtt_sample=50.0)
            
            # 模拟丢包
            cubic.on_loss("triple_duplicate")
            
            # 继续传输
            for i in range(51, 101):
                cubic.on_ack(i, rtt_sample=50.0)
            
            results.append({
                "beta": beta,
                "C": C,
                "final_cwnd": cubic.cwnd,
                "W_max": cubic.W_max
            })
    
    # 显示结果
    print("CUBIC参数调优结果:")
    print("beta   C     最终cwnd   W_max")
    print("-" * 30)
    for result in results:
        print(f"{result['beta']:4.1f}  {result['C']:4.1f}  {result['final_cwnd']:8.2f}  {result['W_max']:8.2f}")
    
    print("\n2. 公平性分析演示")
    print("-" * 40)
    
    # 创建多个流竞争带宽
    num_flows = 3
    flows = []
    
    for i in range(num_flows):
        if i % 2 == 0:
            flow = AlgorithmFactory.create_algorithm("reno", initial_cwnd=1)
            flow.name = f"TCP Reno 流{i+1}"
        else:
            flow = AlgorithmFactory.create_algorithm("cubic", initial_cwnd=1)
            flow.name = f"CUBIC 流{i+1}"
        flows.append(flow)
    
    # 模拟竞争
    print(f"模拟{num_flows}个流竞争带宽:")
    
    for step in range(1, 31):
        # 每个流接收ACK
        for flow in flows:
            flow.on_ack(step, rtt_sample=50.0 + np.random.normal(0, 10))
        
        # 每10步打印状态
        if step % 10 == 0:
            print(f"  第{step}步: ", end="")
            for flow in flows:
                print(f"{flow.name}: cwnd={flow.cwnd:.1f}  ", end="")
            print()
    
    # 计算公平性指数
    cwnds = [flow.cwnd for flow in flows]
    sum_cwnd = sum(cwnds)
    sum_squared = sum(c**2 for c in cwnds)
    
    if sum_squared > 0:
        fairness_index = (sum_cwnd ** 2) / (len(flows) * sum_squared)
        print(f"\n公平性指数 (Jain's Fairness Index): {fairness_index:.3f}")
        print("(1.0表示完全公平，值越小表示越不公平)")


def main():
    """主函数"""
    print("拥塞控制算法综合演示")
    print("=" * 60)
    
    # 创建输出目录
    os.makedirs("demo_output", exist_ok=True)
    
    try:
        # 运行各个演示
        demo_basic_algorithm_comparison()
        demo_loss_scenarios()
        demo_network_simulation()
        demo_advanced_features()
        
        print("\n" + "=" * 60)
        print("演示完成!")
        print("=" * 60)
        print("\n生成的图表和输出文件保存在 demo_output/ 目录")
        print("\n要查看图表，请运行:")
        print("  python -c \"import matplotlib.pyplot as plt; plt.show()\"")
        
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
