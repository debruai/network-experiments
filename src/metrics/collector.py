"""
性能指标收集器
收集和分析拥塞控制算法的性能指标
"""

import time
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np
from enum import Enum


class MetricType(Enum):
    """指标类型"""
    CWND = "cwnd"              # 拥塞窗口
    RTT = "rtt"                # 往返时间
    THROUGHPUT = "throughput"  # 吞吐量
    LOSS_RATE = "loss_rate"    # 丢包率
    FAIRNESS = "fairness"      # 公平性
    UTILIZATION = "utilization"  # 带宽利用率


@dataclass
class MetricSample:
    """指标样本"""
    timestamp: float           # 时间戳
    value: float              # 指标值
    metric_type: MetricType   # 指标类型
    algorithm: str            # 算法名称
    tags: Dict[str, Any] = field(default_factory=dict)  # 附加标签


@dataclass
class AlgorithmComparison:
    """算法比较结果"""
    algorithm1: str
    algorithm2: str
    metrics: Dict[str, Dict[str, float]]  # 指标名称 -> {算法1值, 算法2值, 差异}
    summary: str


class MetricsCollector:
    """
    性能指标收集器
    
    收集、存储和分析拥塞控制算法的性能指标
    """
    
    def __init__(self):
        """初始化指标收集器"""
        self.samples: List[MetricSample] = []
        self.start_time = time.time()
        
        # 统计缓存
        self._statistics_cache: Dict[str, Dict[str, Any]] = {}
    
    def record(self, value: float, metric_type: MetricType, 
               algorithm: str, tags: Optional[Dict[str, Any]] = None) -> None:
        """
        记录指标样本
        
        Args:
            value: 指标值
            metric_type: 指标类型
            algorithm: 算法名称
            tags: 附加标签
        """
        timestamp = time.time() - self.start_time
        
        sample = MetricSample(
            timestamp=timestamp,
            value=value,
            metric_type=metric_type,
            algorithm=algorithm,
            tags=tags or {}
        )
        
        self.samples.append(sample)
        
        # 清除缓存
        self._statistics_cache.clear()
    
    def record_batch(self, samples: List[Tuple[float, MetricType, str, Optional[Dict]]]) -> None:
        """
        批量记录指标样本
        
        Args:
            samples: 样本列表 (值, 类型, 算法, 标签)
        """
        for value, metric_type, algorithm, tags in samples:
            self.record(value, metric_type, algorithm, tags)
    
    def get_samples(self, algorithm: Optional[str] = None, 
                   metric_type: Optional[MetricType] = None,
                   time_range: Optional[Tuple[float, float]] = None) -> List[MetricSample]:
        """
        获取指标样本
        
        Args:
            algorithm: 过滤算法名称
            metric_type: 过滤指标类型
            time_range: 过滤时间范围 (开始时间, 结束时间)
            
        Returns:
            过滤后的样本列表
        """
        filtered = self.samples
        
        if algorithm:
            filtered = [s for s in filtered if s.algorithm == algorithm]
        
        if metric_type:
            filtered = [s for s in filtered if s.metric_type == metric_type]
        
        if time_range:
            start, end = time_range
            filtered = [s for s in filtered if start <= s.timestamp <= end]
        
        return filtered
    
    def get_statistics(self, algorithm: str, metric_type: MetricType,
                      time_range: Optional[Tuple[float, float]] = None) -> Dict[str, float]:
        """
        获取指标统计信息
        
        Args:
            algorithm: 算法名称
            metric_type: 指标类型
            time_range: 时间范围
            
        Returns:
            统计信息字典
        """
        # 生成缓存键
        cache_key = f"{algorithm}_{metric_type.value}_{time_range}"
        
        if cache_key in self._statistics_cache:
            return self._statistics_cache[cache_key]
        
        # 获取样本
        samples = self.get_samples(algorithm, metric_type, time_range)
        
        if not samples:
            stats = {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "median": 0.0,
                "q1": 0.0,
                "q3": 0.0
            }
        else:
            values = [s.value for s in samples]
            
            stats = {
                "count": len(values),
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "median": float(np.median(values)),
                "q1": float(np.percentile(values, 25)),
                "q3": float(np.percentile(values, 75))
            }
        
        # 缓存结果
        self._statistics_cache[cache_key] = stats
        
        return stats
    
    def compare_algorithms(self, algorithm1: str, algorithm2: str,
                          metric_types: Optional[List[MetricType]] = None) -> AlgorithmComparison:
        """
        比较两个算法的性能
        
        Args:
            algorithm1: 第一个算法名称
            algorithm2: 第二个算法名称
            metric_types: 要比较的指标类型列表，如果为None则比较所有指标
            
        Returns:
            算法比较结果
        """
        if metric_types is None:
            metric_types = [mt for mt in MetricType]
        
        comparison_metrics = {}
        
        for metric_type in metric_types:
            stats1 = self.get_statistics(algorithm1, metric_type)
            stats2 = self.get_statistics(algorithm2, metric_type)
            
            # 计算差异（算法2相对于算法1）
            if stats1["count"] > 0 and stats2["count"] > 0:
                mean_diff = stats2["mean"] - stats1["mean"]
                mean_diff_pct = (mean_diff / stats1["mean"] * 100) if stats1["mean"] != 0 else 0
                
                comparison_metrics[metric_type.value] = {
                    algorithm1: stats1["mean"],
                    algorithm2: stats2["mean"],
                    "difference": mean_diff,
                    "difference_percent": mean_diff_pct,
                    "better_algorithm": algorithm2 if mean_diff > 0 else algorithm1
                }
        
        # 生成总结
        summary = self._generate_comparison_summary(algorithm1, algorithm2, comparison_metrics)
        
        return AlgorithmComparison(
            algorithm1=algorithm1,
            algorithm2=algorithm2,
            metrics=comparison_metrics,
            summary=summary
        )
    
    def _generate_comparison_summary(self, algo1: str, algo2: str, 
                                    metrics: Dict[str, Dict[str, float]]) -> str:
        """生成比较总结"""
        if not metrics:
            return "没有可比较的指标数据"
        
        # 统计哪个算法在更多指标上表现更好
        algo1_wins = 0
        algo2_wins = 0
        ties = 0
        
        for metric_data in metrics.values():
            better_algo = metric_data.get("better_algorithm", "")
            if better_algo == algo1:
                algo1_wins += 1
            elif better_algo == algo2:
                algo2_wins += 1
            else:
                ties += 1
        
        # 生成总结
        lines = []
        lines.append(f"算法比较: {algo1} vs {algo2}")
        lines.append(f"比较指标数: {len(metrics)}")
        lines.append(f"{algo1} 表现更好的指标数: {algo1_wins}")
        lines.append(f"{algo2} 表现更好的指标数: {algo2_wins}")
        lines.append(f"平局指标数: {ties}")
        
        # 添加关键指标比较
        key_metrics = ["throughput", "loss_rate", "cwnd"]
        for key in key_metrics:
            if key in metrics:
                data = metrics[key]
                lines.append(f"\n{key.upper()}:")
                lines.append(f"  {algo1}: {data[algo1]:.4f}")
                lines.append(f"  {algo2}: {data[algo2]:.4f}")
                lines.append(f"  差异: {data['difference']:+.4f} ({data['difference_percent']:+.1f}%)")
                lines.append(f"  更好的算法: {data['better_algorithm']}")
        
        return "\n".join(lines)
    
    def calculate_fairness_index(self, algorithms: List[str], 
                                time_range: Optional[Tuple[float, float]] = None) -> float:
        """
        计算公平性指数 (Jain's Fairness Index)
        
        Args:
            algorithms: 算法名称列表
            time_range: 时间范围
            
        Returns:
            公平性指数 (0.0-1.0)
        """
        throughputs = []
        
        for algo in algorithms:
            stats = self.get_statistics(algo, MetricType.THROUGHPUT, time_range)
            if stats["count"] > 0:
                throughputs.append(stats["mean"])
        
        if not throughputs:
            return 0.0
        
        # Jain's Fairness Index: (Σx_i)² / (n * Σx_i²)
        sum_throughput = sum(throughputs)
        sum_squared_throughput = sum(t**2 for t in throughputs)
        n = len(throughputs)
        
        if sum_squared_throughput == 0:
            return 0.0
        
        fairness = (sum_throughput ** 2) / (n * sum_squared_throughput)
        
        # 记录公平性指标
        for algo in algorithms:
            self.record(fairness, MetricType.FAIRNESS, algo, {"algorithms": algorithms})
        
        return fairness
    
    def calculate_convergence_time(self, algorithm: str, metric_type: MetricType,
                                  target_value: float, tolerance: float = 0.1) -> Optional[float]:
        """
        计算收敛时间
        
        Args:
            algorithm: 算法名称
            metric_type: 指标类型
            target_value: 目标值
            tolerance: 容忍度 (相对误差)
            
        Returns:
            收敛时间 (秒)，如果未收敛则返回None
        """
        samples = self.get_samples(algorithm, metric_type)
        
        if not samples:
            return None
        
        # 按时间排序
        samples.sort(key=lambda s: s.timestamp)
        
        # 找到第一个进入容忍范围的样本
        for sample in samples:
            relative_error = abs(sample.value - target_value) / target_value
            if relative_error <= tolerance:
                return sample.timestamp
        
        return None
    
    def export_to_csv(self, filepath: str) -> None:
        """
        导出指标数据到CSV文件
        
        Args:
            filepath: CSV文件路径
        """
        import csv
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'value', 'metric_type', 'algorithm', 'tags']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for sample in self.samples:
                writer.writerow({
                    'timestamp': sample.timestamp,
                    'value': sample.value,
                    'metric_type': sample.metric_type.value,
                    'algorithm': sample.algorithm,
                    'tags': str(sample.tags)
                })
    
    def get_total_samples(self) -> int:
        """
        获取总样本数
        
        Returns:
            总样本数
        """
        return len(self.samples)
    
    def reset(self) -> None:
        """重置收集器"""
        self.samples.clear()
        self._statistics_cache.clear()
        self.start_time = time.time()
    
    def __str__(self) -> str:
        """返回收集器状态字符串表示"""
        algorithms = set(s.algorithm for s in self.samples)
        metric_types = set(s.metric_type for s in self.samples)
        
        return (f"MetricsCollector: "
                f"样本数={len(self.samples)}, "
                f"算法={len(algorithms)}, "
                f"指标类型={len(metric_types)}")


# 使用示例
if __name__ == "__main__":
    print("=== 性能指标收集器演示 ===\n")
    
    # 创建收集器
    collector = MetricsCollector()
    
    # 模拟记录一些指标
    print("记录指标样本...")
    
    # 记录TCP Reno指标
    for i in range(10):
        collector.record(
            value=10.0 + i * 0.5 + np.random.normal(0, 0.1),
            metric_type=MetricType.THROUGHPUT,
            algorithm="TCP Reno",
            tags={"iteration": i, "network": "stable"}
        )
        
        collector.record(
            value=50.0 + np.random.normal(0, 5),
            metric_type=MetricType.RTT,
            algorithm="TCP Reno",
            tags={"iteration": i}
        )
    
    # 记录CUBIC指标
    for i in range(10):
        collector.record(
            value=12.0 + i * 0.7 + np.random.normal(0, 0.1),
            metric_type=MetricType.THROUGHPUT,
            algorithm="CUBIC",
            tags={"iteration": i, "network": "stable"}
        )
        
        collector.record(
            value=45.0 + np.random.normal(0, 3),
            metric_type=MetricType.RTT,
            algorithm="CUBIC",
            tags={"iteration": i}
        )
    
    print(f"收集器状态: {collector}\n")
    
    # 获取统计信息
    print("TCP Reno吞吐量统计:")
    reno_stats = collector.get_statistics("TCP Reno", MetricType.THROUGHPUT)
    for key, value in reno_stats.items():
        print(f"  {key}: {value:.4f}")
    
    print("\nCUBIC吞吐量统计:")
    cubic_stats = collector.get_statistics("CUBIC", MetricType.THROUGHPUT)
    for key, value in cubic_stats.items():
        print(f"  {key}: {value:.4f}")
    
    # 比较算法
    print("\n算法比较:")
    comparison = collector.compare_algorithms("TCP Reno", "CUBIC")
    print(comparison.summary)
    
    # 计算公平性指数
    print("\n公平性指数计算:")
    fairness = collector.calculate_fairness_index(["TCP Reno", "CUBIC"])
    print(f"Jain's Fairness Index: {fairness:.4f}")
    
    # 计算收敛时间
    print("\n收敛时间计算:")
    convergence_time = collector.calculate_convergence_time(
        "TCP Reno", MetricType.THROUGHPUT, target_value=12.0
    )
    if convergence_time:
        print(f"TCP Reno收敛到12.0 Mbps的时间: {convergence_time:.2f}秒")
    else:
        print("TCP Reno未收敛到目标值")
