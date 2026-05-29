"""
CUBIC拥塞控制算法实现
立方拥塞控制算法，适用于高速网络
"""

from typing import Optional
from .base import CongestionControl
import time
import math


class CUBIC(CongestionControl):
    """
    CUBIC拥塞控制算法
    
    算法特点：
    1. 立方增长函数：W(t) = C×(t-K)³ + W_max
    2. 窗口增长依赖两次丢包时间间隔
    3. 更好的RTT公平性
    4. 适应高带宽延迟积网络
    """
    
    def __init__(self, mss: int = 1460, initial_cwnd: int = 1, 
                 beta: float = 0.7, C: float = 0.4):
        """
        初始化CUBIC算法
        
        Args:
            mss: 最大报文段大小 (字节)
            initial_cwnd: 初始拥塞窗口 (MSS数量)
            beta: 乘性减因子 (默认0.7)
            C: 立方缩放因子 (默认0.4)
        """
        super().__init__(mss, initial_cwnd)
        
        # CUBIC特定参数
        self.beta = beta  # 乘性减因子
        self.C = C        # 立方缩放因子
        
        # CUBIC状态变量
        self.W_max = 0.0      # 最近丢包前的窗口大小
        self.K = 0.0          # 窗口回到W_max所需时间
        self.t = 0.0          # 距离上次丢包的时间
        self.epoch_start = 0.0  # 当前epoch开始时间
        self.origin_point = 0.0  # 原点窗口大小
        
        # 快速收敛优化
        self.fast_convergence = True
        self.W_last_max = 0.0  # 上一次的W_max
        
        # TCP友好模式（在低速时使用类似TCP的窗口增长）
        self.tcp_friendly = True
        self.tcp_cwnd = 0.0   # TCP友好模式的窗口估计
        
    def on_ack(self, ack_number: int, rtt_sample: Optional[float] = None) -> None:
        """
        收到ACK时的处理
        
        Args:
            ack_number: 确认的序列号
            rtt_sample: RTT采样值 (可选)
        """
        # 更新RTT估计
        if rtt_sample is not None:
            self.update_rtt(rtt_sample)
        
        # 处理重复ACK
        if ack_number <= self.last_ack:
            self.dup_acks += 1
            if self.dup_acks == 3:
                self.on_loss("triple_duplicate")
        else:
            # 新的ACK
            self.dup_acks = 0
            self.last_ack = ack_number
        
        # 更新拥塞窗口
        self.update_cwnd()
        
        # 记录指标
        self.record_metrics()
    
    def on_loss(self, loss_type: str = "timeout") -> None:
        """
        检测到丢包时的处理
        
        Args:
            loss_type: 丢包类型 ("timeout" 或 "triple_duplicate")
        """
        current_time = time.time() - self.start_time
        
        if loss_type == "timeout":
            self._handle_timeout(current_time)
        elif loss_type == "triple_duplicate":
            self._handle_triple_duplicate(current_time)
        
        # 记录丢包事件
        self.metrics.loss_rate += 1
    
    def update_cwnd(self) -> None:
        """更新拥塞窗口（使用CUBIC算法）"""
        current_time = time.time() - self.start_time
        
        # 更新距离上次丢包的时间
        self.t = current_time - self.epoch_start
        
        # 计算CUBIC窗口
        cubic_cwnd = self._cubic_window(self.t)
        
        # TCP友好窗口（用于低速网络）
        if self.tcp_friendly:
            self.tcp_cwnd = self._tcp_friendly_window()
            # 选择较大的窗口
            self.cwnd = max(cubic_cwnd, self.tcp_cwnd)
        else:
            self.cwnd = cubic_cwnd
        
        # 窗口大小不能小于1个MSS
        self.cwnd = max(1.0, self.cwnd)
    
    def _cubic_window(self, t: float) -> float:
        """
        计算CUBIC窗口大小
        
        Args:
            t: 距离上次丢包的时间
            
        Returns:
            窗口大小 (MSS数量)
        """
        # 计算K：窗口回到W_max所需时间
        # K = 立方根(W_max * (1 - beta) / C)
        if self.W_max > 0:
            self.K = math.pow(self.W_max * (1 - self.beta) / self.C, 1.0/3.0)
        else:
            self.K = 0
        
        # 计算窗口偏移量
        if t < self.K:
            # 在K之前：凸增长
            offset = self.K - t
            return self.C * math.pow(offset, 3) + self.W_max
        else:
            # 在K之后：凹增长
            offset = t - self.K
            return self.C * math.pow(offset, 3) + self.W_max
    
    def _tcp_friendly_window(self) -> float:
        """
        计算TCP友好窗口（用于低速网络）
        
        Returns:
            TCP友好窗口大小
        """
        # 估计TCP Reno在相同条件下的窗口
        # 假设TCP Reno每RTT增加1个MSS
        rtt_seconds = self.rtt / 1000.0  # 转换为秒
        
        if rtt_seconds <= 0:
            return 1.0
        
        # 简单估计：窗口增长率为1/RTT
        elapsed_time = time.time() - self.start_time
        tcp_window = 1.0 + elapsed_time / rtt_seconds
        
        return tcp_window
    
    def _handle_timeout(self, current_time: float) -> None:
        """处理超时丢包"""
        # 保存当前窗口作为W_max
        self._update_W_max()
        
        # 重置窗口
        self.cwnd = 1.0
        
        # 重置epoch
        self.epoch_start = current_time
        self.t = 0.0
        
        # 重置状态
        self.state = "slow_start"
        self.dup_acks = 0
    
    def _handle_triple_duplicate(self, current_time: float) -> None:
        """处理三个重复ACK（快速重传）"""
        # 保存当前窗口作为W_max
        self._update_W_max()
        
        # 快速收敛优化
        if self.fast_convergence and self.W_last_max > 0 and self.W_max < self.W_last_max:
            # 进一步减小窗口以加速收敛
            self.W_max = self.W_max * (1.0 + self.beta) / 2.0
        else:
            self.W_last_max = self.W_max
        
        # 减小窗口（乘性减）
        self.cwnd = self.cwnd * self.beta
        
        # 重置epoch
        self.epoch_start = current_time
        self.t = 0.0
        
        # 更新状态
        self.state = "fast_recovery"
    
    def _update_W_max(self) -> None:
        """更新W_max（最近丢包前的窗口大小）"""
        if self.cwnd > self.W_max:
            self.W_max = self.cwnd
    
    def reset(self) -> None:
        """重置算法状态"""
        super().reset()
        self.W_max = 0.0
        self.K = 0.0
        self.t = 0.0
        self.epoch_start = 0.0
        self.origin_point = 0.0
        self.W_last_max = 0.0
        self.tcp_cwnd = 0.0
    
    def get_parameters(self) -> dict:
        """获取CUBIC算法参数"""
        return {
            "beta": self.beta,
            "C": self.C,
            "W_max": self.W_max,
            "K": self.K,
            "t": self.t,
            "fast_convergence": self.fast_convergence,
            "tcp_friendly": self.tcp_friendly
        }
    
    def __str__(self) -> str:
        """返回算法状态字符串表示"""
        base_str = super().__str__()
        params = self.get_parameters()
        return (f"{base_str}, "
                f"W_max={params['W_max']:.2f}, "
                f"K={params['K']:.2f}, "
                f"t={params['t']:.2f}s")


# 示例：使用CUBIC算法
if __name__ == "__main__":
    # 创建CUBIC实例
    cubic = CUBIC(beta=0.7, C=0.4)
    
    print("初始状态:", cubic)
    print("参数:", cubic.get_parameters())
    
    # 模拟收到ACK
    print("\n模拟网络传输...")
    for i in range(1, 21):
        # 模拟RTT在40-60ms之间变化
        rtt = 50.0 + (i % 3 - 1) * 10.0
        cubic.on_ack(i, rtt_sample=rtt)
        
        if i % 5 == 0:
            print(f"ACK {i}: {cubic}")
    
    # 模拟丢包（三个重复ACK）
    print("\n模拟三个重复ACK丢包...")
    cubic.on_loss("triple_duplicate")
    print("丢包后:", cubic)
    print("参数:", cubic.get_parameters())
    
    # 继续传输
    print("\n继续传输...")
    for i in range(21, 31):
        cubic.on_ack(i, rtt_sample=50.0)
    
    print("最终状态:", cubic)
    
    # 获取性能指标
    metrics = cubic.get_current_metrics()
    print(f"\n性能指标: 平均cwnd={metrics.avg_cwnd:.2f}, RTT={metrics.rtt:.1f}ms")
    
    # 对比不同beta值的影响
    print("\n--- 不同beta值对比 ---")
    for beta in [0.5, 0.7, 0.8]:
        test_cubic = CUBIC(beta=beta)
        for i in range(1, 11):
            test_cubic.on_ack(i, rtt_sample=50.0)
        test_cubic.on_loss("triple_duplicate")
        print(f"beta={beta}: 丢包后cwnd={test_cubic.cwnd:.2f}")
