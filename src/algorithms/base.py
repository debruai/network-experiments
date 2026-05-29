"""
拥塞控制算法基类
定义所有拥塞控制算法的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class AlgorithmMetrics:
    """算法性能指标"""
    throughput: float = 0.0  # 吞吐量 (Mbps)
    avg_cwnd: float = 0.0    # 平均拥塞窗口
    loss_rate: float = 0.0   # 丢包率
    rtt: float = 0.0         # 平均往返时间
    fairness_index: float = 0.0  # 公平性指数
    convergence_time: float = 0.0  # 收敛时间


@dataclass
class NetworkConditions:
    """网络条件"""
    bandwidth: float = 10.0      # 带宽 (Mbps)
    delay: float = 50.0          # 延迟 (ms)
    loss_probability: float = 0.0  # 丢包概率
    mtu: int = 1500              # 最大传输单元 (字节)
    buffer_size: int = 100       # 缓冲区大小 (数据包数)


class CongestionControl(ABC):
    """
    拥塞控制算法抽象基类
    所有具体算法必须实现这些方法
    """
    
    def __init__(self, mss: int = 1460, initial_cwnd: int = 1):
        """
        初始化拥塞控制算法
        
        Args:
            mss: 最大报文段大小 (字节)
            initial_cwnd: 初始拥塞窗口 (MSS数量)
        """
        self.mss = mss  # 最大报文段大小
        self.cwnd = float(initial_cwnd)  # 当前拥塞窗口 (MSS数量)
        self.ssthresh = float('inf')     # 慢启动阈值
        self.rtt = 100.0                 # 当前RTT估计 (ms)
        self.rtt_var = 50.0              # RTT变化量
        self.dup_acks = 0                # 重复ACK计数
        self.last_ack = 0                # 最后确认的序列号
        self.state = "slow_start"        # 当前状态
        self.start_time = time.time()    # 算法开始时间
        
        # 性能指标
        self.metrics = AlgorithmMetrics()
        self.cwnd_history = []           # 拥塞窗口历史记录
        self.rtt_history = []            # RTT历史记录
        
    @abstractmethod
    def on_ack(self, ack_number: int, rtt_sample: Optional[float] = None) -> None:
        """
        收到ACK时的处理
        
        Args:
            ack_number: 确认的序列号
            rtt_sample: RTT采样值 (可选)
        """
        pass
    
    @abstractmethod
    def on_loss(self, loss_type: str = "timeout") -> None:
        """
        检测到丢包时的处理
        
        Args:
            loss_type: 丢包类型 ("timeout" 或 "triple_duplicate")
        """
        pass
    
    @abstractmethod
    def update_cwnd(self) -> None:
        """更新拥塞窗口"""
        pass
    
    def update_rtt(self, rtt_sample: float) -> None:
        """
        更新RTT估计 (使用TCP的RTT估计算法)
        
        Args:
            rtt_sample: 新的RTT采样值
        """
        if rtt_sample <= 0:
            return
            
        alpha = 0.125  # RTT平滑因子
        beta = 0.25    # RTT变化量平滑因子
        
        # 更新RTT估计
        self.rtt = (1 - alpha) * self.rtt + alpha * rtt_sample
        # 更新RTT变化量
        self.rtt_var = (1 - beta) * self.rtt_var + beta * abs(rtt_sample - self.rtt)
        
        self.rtt_history.append((time.time() - self.start_time, self.rtt))
    
    def get_timeout_interval(self) -> float:
        """
        计算重传超时时间 (RTO)
        使用标准TCP算法: RTO = RTT + 4 * RTT_VAR
        
        Returns:
            重传超时时间 (ms)
        """
        return self.rtt + 4 * self.rtt_var
    
    def record_metrics(self) -> None:
        """记录当前性能指标"""
        self.cwnd_history.append((time.time() - self.start_time, self.cwnd))
    
    def get_current_metrics(self) -> AlgorithmMetrics:
        """
        获取当前性能指标
        
        Returns:
            算法性能指标
        """
        if len(self.cwnd_history) > 0:
            times, cwnds = zip(*self.cwnd_history[-100:])  # 最近100个样本
            self.metrics.avg_cwnd = sum(cwnds) / len(cwnds)
        
        if len(self.rtt_history) > 0:
            _, rtts = zip(*self.rtt_history[-100:])
            self.metrics.rtt = sum(rtts) / len(rtts)
            
        return self.metrics
    
    def reset(self) -> None:
        """重置算法状态"""
        self.cwnd = 1.0
        self.ssthresh = float('inf')
        self.dup_acks = 0
        self.state = "slow_start"
        self.start_time = time.time()
        self.cwnd_history.clear()
        self.rtt_history.clear()
    
    def __str__(self) -> str:
        """返回算法状态字符串表示"""
        return (f"{self.__class__.__name__}: "
                f"cwnd={self.cwnd:.2f}, "
                f"ssthresh={self.ssthresh if self.ssthresh < float('inf') else 'inf'}, "
                f"state={self.state}, "
                f"rtt={self.rtt:.1f}ms")
