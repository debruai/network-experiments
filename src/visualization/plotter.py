"""
数据可视化工具
绘制拥塞控制算法的性能图表
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..metrics.collector import MetricsCollector, MetricType, MetricSample

# 导入字体配置
try:
    from .font_config import configure_chinese_fonts
    CHINESE_FONTS_AVAILABLE = True
except ImportError:
    CHINESE_FONTS_AVAILABLE = False


@dataclass
class PlotConfig:
    """绘图配置"""
    title: str = "拥塞控制算法性能"
    xlabel: str = "时间 (秒)"
    ylabel: str = "值"
    figsize: Tuple[int, int] = (12, 8)
    dpi: int = 100
    grid: bool = True
    legend: bool = True
    save_path: Optional[str] = None
    show: bool = True


class MetricsPlotter:
    """
    指标绘图器
    
    绘制拥塞控制算法的性能图表
    """
    
    def __init__(self, collector: MetricsCollector):
        """
        初始化绘图器
        
        Args:
            collector: 指标收集器
        """
        self.collector = collector
        
        # 配置中文字体
        self._configure_fonts()
    
    def _configure_fonts(self):
        """配置中文字体"""
        if CHINESE_FONTS_AVAILABLE:
            try:
                configure_chinese_fonts()
            except Exception as e:
                print(f"字体配置失败: {e}")
                # 回退到简单配置
                try:
                    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False
                except:
                    pass
        else:
            # 简单字体配置
            try:
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']
                plt.rcParams['axes.unicode_minus'] = False
            except:
                pass
    
    def plot_metric_timeseries(self, algorithms: List[str], 
                              metric_type: MetricType,
                              config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制指标时间序列图
        
        Args:
            algorithms: 算法名称列表
            metric_type: 指标类型
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if config is None:
            config = PlotConfig()
        
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
        
        for algo in algorithms:
            samples = self.collector.get_samples(algo, metric_type)
            
            if not samples:
                continue
            
            # 按时间排序
            samples.sort(key=lambda s: s.timestamp)
            
            times = [s.timestamp for s in samples]
            values = [s.value for s in samples]
            
            ax.plot(times, values, label=algo, marker='o', markersize=3, linewidth=2)
        
        # 设置图表属性
        ax.set_title(config.title, fontsize=16, fontweight='bold')
        ax.set_xlabel(config.xlabel, fontsize=12)
        ax.set_ylabel(config.ylabel, fontsize=12)
        
        if config.grid:
            ax.grid(True, linestyle='--', alpha=0.7)
        
        if config.legend:
            ax.legend(fontsize=10)
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图表
        if config.save_path:
            plt.savefig(config.save_path, dpi=config.dpi, bbox_inches='tight')
        
        if config.show:
            plt.show()
        
        return fig
    
    def plot_cwnd_comparison(self, algorithms: List[str],
                            config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制拥塞窗口比较图
        
        Args:
            algorithms: 算法名称列表
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if config is None:
            config = PlotConfig(
                title="拥塞窗口随时间变化",
                ylabel="拥塞窗口 (MSS)"
            )
        
        return self.plot_metric_timeseries(algorithms, MetricType.CWND, config)
    
    def plot_throughput_comparison(self, algorithms: List[str],
                                  config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制吞吐量比较图
        
        Args:
            algorithms: 算法名称列表
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if config is None:
            config = PlotConfig(
                title="吞吐量随时间变化",
                ylabel="吞吐量 (Mbps)"
            )
        
        return self.plot_metric_timeseries(algorithms, MetricType.THROUGHPUT, config)
    
    def plot_rtt_comparison(self, algorithms: List[str],
                           config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制RTT比较图
        
        Args:
            algorithms: 算法名称列表
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if config is None:
            config = PlotConfig(
                title="往返时间随时间变化",
                ylabel="RTT (ms)"
            )
        
        return self.plot_metric_timeseries(algorithms, MetricType.RTT, config)
    
    def plot_boxplot_comparison(self, algorithms: List[str],
                               metric_types: Optional[List[MetricType]] = None,
                               config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制箱线图比较
        
        Args:
            algorithms: 算法名称列表
            metric_types: 要比较的指标类型列表
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if metric_types is None:
            metric_types = [MetricType.THROUGHPUT, MetricType.RTT, MetricType.CWND]
        
        if config is None:
            config = PlotConfig(
                title="算法性能箱线图比较",
                xlabel="算法",
                ylabel="值",
                figsize=(14, 10)
            )
        
        n_metrics = len(metric_types)
        fig, axes = plt.subplots(1, n_metrics, figsize=config.figsize, dpi=config.dpi)
        
        if n_metrics == 1:
            axes = [axes]
        
        for idx, metric_type in enumerate(metric_types):
            ax = axes[idx]
            
            # 收集数据
            data = []
            labels = []
            
            for algo in algorithms:
                samples = self.collector.get_samples(algo, metric_type)
                if samples:
                    values = [s.value for s in samples]
                    data.append(values)
                    labels.append(algo)
            
            # 绘制箱线图
            box = ax.boxplot(data, labels=labels, patch_artist=True)
            
            # 设置箱线图颜色
            colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
            for patch, color in zip(box['boxes'], colors):
                patch.set_facecolor(color)
            
            # 设置子图属性
            ax.set_title(f"{metric_type.value.upper()} 分布", fontsize=12, fontweight='bold')
            ax.set_xlabel(config.xlabel, fontsize=10)
            ax.set_ylabel(metric_type.value, fontsize=10)
            
            if config.grid:
                ax.grid(True, linestyle='--', alpha=0.5)
            
            # 旋转x轴标签
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 设置总标题
        fig.suptitle(config.title, fontsize=16, fontweight='bold')
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图表
        if config.save_path:
            plt.savefig(config.save_path, dpi=config.dpi, bbox_inches='tight')
        
        if config.show:
            plt.show()
        
        return fig
    
    def plot_algorithm_state_machine(self, algorithm: str,
                                    config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制算法状态机转换图
        
        Args:
            algorithm: 算法名称
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if config is None:
            config = PlotConfig(
                title=f"{algorithm} 状态转换",
                figsize=(10, 8),
                xlabel="时间 (秒)",
                ylabel="状态"
            )
        
        # 获取状态转换事件（这里需要从收集器中获取状态转换数据）
        # 由于我们的收集器目前不记录状态转换，这里先创建一个示例
        
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
        
        # 示例数据 - 在实际使用中应从收集器获取
        states = ["slow_start", "congestion_avoidance", "fast_recovery", "slow_start"]
        state_times = [0, 5, 10, 15]
        
        # 创建状态映射
        state_mapping = {
            "slow_start": 0,
            "congestion_avoidance": 1,
            "fast_recovery": 2
        }
        
        # 绘制状态阶梯图
        state_values = [state_mapping.get(s, 0) for s in states]
        
        ax.step(state_times, state_values, where='post', linewidth=3, marker='o', markersize=8)
        
        # 设置y轴标签
        ax.set_yticks(list(state_mapping.values()))
        ax.set_yticklabels(list(state_mapping.keys()))
        
        # 设置图表属性
        ax.set_title(config.title, fontsize=16, fontweight='bold')
        ax.set_xlabel(config.xlabel, fontsize=12)
        ax.set_ylabel(config.ylabel, fontsize=12)
        
        if config.grid:
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图表
        if config.save_path:
            plt.savefig(config.save_path, dpi=config.dpi, bbox_inches='tight')
        
        if config.show:
            plt.show()
        
        return fig
    
    def plot_performance_summary(self, algorithms: List[str],
                                config: Optional[PlotConfig] = None) -> plt.Figure:
        """
        绘制性能总结雷达图
        
        Args:
            algorithms: 算法名称列表
            config: 绘图配置
            
        Returns:
            matplotlib图形对象
        """
        if config is None:
            config = PlotConfig(
                title="算法性能雷达图",
                figsize=(10, 10)
            )
        
        # 定义要比较的指标
        metrics = [
            ("吞吐量", MetricType.THROUGHPUT, True),   # 越高越好
            ("丢包率", MetricType.LOSS_RATE, False),   # 越低越好
            ("RTT", MetricType.RTT, False),           # 越低越好
            ("公平性", MetricType.FAIRNESS, True),     # 越高越好
            ("cwnd稳定性", MetricType.CWND, False)     # 变异系数越小越好
        ]
        
        fig = plt.figure(figsize=config.figsize, dpi=config.dpi)
        ax = fig.add_subplot(111, projection='polar')
        
        # 计算角度
        n_metrics = len(metrics)
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        # 为每个算法绘制雷达图
        colors = plt.cm.tab10(np.linspace(0, 1, len(algorithms)))
        
        for algo_idx, algo in enumerate(algorithms):
            values = []
            
            for metric_name, metric_type, higher_is_better in metrics:
                stats = self.collector.get_statistics(algo, metric_type)
                
                if stats["count"] == 0:
                    value = 0
                else:
                    value = stats["mean"]
                    
                    # 对于越低越好的指标，取倒数（归一化处理）
                    if not higher_is_better and value != 0:
                        value = 1 / value
                
                # 归一化到0-1范围（简化处理）
                values.append(min(max(value / 100, 0), 1) if value != 0 else 0)
            
            values += values[:1]  # 闭合图形
            
            ax.plot(angles, values, 'o-', linewidth=2, label=algo, color=colors[algo_idx])
            ax.fill(angles, values, alpha=0.1, color=colors[algo_idx])
        
        # 设置雷达图属性
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m[0] for m in metrics], fontsize=10)
        ax.set_ylim(0, 1)
        
        # 设置标题和图例
        ax.set_title(config.title, fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图表
        if config.save_path:
            plt.savefig(config.save_path, dpi=config.dpi, bbox_inches='tight')
        
        if config.show:
            plt.show()
        
        return fig
    
    def save_all_plots(self, algorithms: List[str], output_dir: str) -> Dict[str, str]:
        """
        保存所有图表到指定目录
        
        Args:
            algorithms: 算法名称列表
            output_dir: 输出目录
            
        Returns:
            保存的文件路径字典
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # 1. 拥塞窗口图
        cwnd_path = output_path / "cwnd_comparison.png"
        self.plot_cwnd_comparison(algorithms, PlotConfig(
            title="拥塞窗口比较",
            save_path=str(cwnd_path),
            show=False
        ))
        saved_files["cwnd"] = str(cwnd_path)
        
        # 2. 吞吐量图
        throughput_path = output_path / "throughput_comparison.png"
        self.plot_throughput_comparison(algorithms, PlotConfig(
            title="吞吐量比较",
            save_path=str(throughput_path),
            show=False
        ))
        saved_files["throughput"] = str(throughput_path)
        
        # 3. RTT图
        rtt_path = output_path / "rtt_comparison.png"
        self.plot_rtt_comparison(algorithms, PlotConfig(
            title="RTT比较",
            save_path=str(rtt_path),
            show=False
        ))
        saved_files["rtt"] = str(rtt_path)
        
        # 4. 箱线图
        boxplot_path = output_path / "boxplot_comparison.png"
        self.plot_boxplot_comparison(algorithms, config=PlotConfig(
            title="性能箱线图比较",
            save_path=str(boxplot_path),
            show=False
        ))
        saved_files["boxplot"] = str(boxplot_path)
        
        # 5. 雷达图
        radar_path = output_path / "radar_comparison.png"
        self.plot_performance_summary(algorithms, PlotConfig(
            title="性能雷达图",
            save_path=str(radar_path),
            show=False
        ))
        saved_files["radar"] = str(radar_path)
        
        return saved_files


# 使用示例
if __name__ == "__main__":
    print("=== 数据可视化工具演示 ===\n")
    
    # 创建模拟数据
    from ..metrics.collector import MetricsCollector, MetricType
    
    collector = MetricsCollector()
    
    # 生成模拟数据
    np.random.seed(42)
    
    algorithms = ["TCP Reno", "CUBIC"]
    
    for algo in algorithms:
        # 模拟拥塞窗口数据
        for t in np.linspace(0, 30, 100):
            if algo == "TCP Reno":
                cwnd = 10 + 5 * np.sin(t/5) + np.random.normal(0, 1)
            else:
                cwnd = 15 + 3 * np.sin(t/3) + np.random.normal(0, 0.8)
            
            collector.record(cwnd, MetricType.CWND, algo, {"time": t})
        
        # 模拟吞吐量数据
        for t in np.linspace(0, 30, 50):
            if algo == "TCP Reno":
                throughput = 8 + 2 * np.sin(t/7) + np.random.normal(0, 0.3)
            else:
                throughput = 10 + 1.5 * np.sin(t/4) + np.random.normal(0, 0.2)
            
            collector.record(throughput, MetricType.THROUGHPUT, algo, {"time": t})
        
        # 模拟RTT数据
        for t in np.linspace(0, 30, 80):
            if algo == "TCP Reno":
                rtt = 50 + 10 * np.sin(t/6) + np.random.normal(0, 3)
            else:
                rtt = 45 + 8 * np.sin(t/5) + np.random.normal(0, 2)
            
            collector.record(rtt, MetricType.RTT, algo, {"time": t})
    
    print(f"收集了 {len(collector.samples)} 个样本")
    
    # 创建绘图器
    plotter = MetricsPlotter(collector)
    
    # 绘制各种图表
    print("\n1. 绘制拥塞窗口比较图...")
    plotter.plot_cwnd_comparison(algorithms)
    
    print("\n2. 绘制吞吐量比较图...")
    plotter.plot_throughput_comparison(algorithms)
    
    print("\n3. 绘制RTT比较图...")
    plotter.plot_rtt_comparison(algorithms)
    
    print("\n4. 绘制箱线图比较...")
    plotter.plot_boxplot_comparison(algorithms)
    
    print("\n5. 绘制性能雷达图...")
    plotter.plot_performance_summary(algorithms)
    
    print("\n6. 保存所有图表到文件...")
    saved_files = plotter.save_all_plots(algorithms, "output_plots")
    
    print("保存的文件:")
    for plot_type, filepath in saved_files.items():
        print(f"  {plot_type}: {filepath}")
    
    print("\n可视化演示完成!")
