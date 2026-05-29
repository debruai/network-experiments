"""
TCP Reno拥塞控制算法实现
包含慢启动、拥塞避免、快速重传、快速恢复
"""

from typing import Optional
from .base import CongestionControl
import time


class TCPReno(CongestionControl):
    """
    TCP Reno拥塞控制算法
    
    算法特点：
    1. 慢启动：cwnd指数增长
    2. 拥塞避免：cwnd线性增长
    3. 快速重传：收到3个重复ACK立即重传
    4. 快速恢复：cwnd减半后进入恢复阶段
    """
    
    def __init__(self, mss: int = 1460, initial_cwnd: int = 1):
        """
        初始化TCP Reno算法
        
        Args:
            mss: 最大报文段大小 (字节)
            initial_cwnd: 初始拥塞窗口 (MSS数量)
        """
        super().__init__(mss, initial_cwnd)
        self.recovery_point = 0  # 快速恢复点
        self.in_fast_recovery = False  # 是否在快速恢复中
        self.ack_count = 0  # ACK计数器（用于拥塞避免）
        
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
            self._handle_duplicate_ack()
        else:
            # 新的ACK
            self.dup_acks = 0
            self.last_ack = ack_number
            
            if self.in_fast_recovery:
                self._handle_new_ack_in_recovery(ack_number)
            else:
                self._handle_new_ack(ack_number)
        
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
        if loss_type == "timeout":
            self._handle_timeout()
        elif loss_type == "triple_duplicate":
            self._handle_triple_duplicate()
    
    def update_cwnd(self) -> None:
        """更新拥塞窗口（根据当前状态）"""
        # 窗口大小不能小于1个MSS
        self.cwnd = max(1.0, self.cwnd)
        
        # 如果处于快速恢复状态，窗口更新在_handle_duplicate_ack中处理
        if not self.in_fast_recovery:
            if self.state == "slow_start":
                # 慢启动：每收到一个ACK，cwnd增加1个MSS
                # 实际增长在_handle_new_ack中处理
                pass
            elif self.state == "congestion_avoidance":
                # 拥塞避免：每RTT增加1个MSS
                # 实际增长在_handle_new_ack中处理
                pass
    
    def _handle_new_ack(self, ack_number: int) -> None:
        """处理新的ACK"""
        if self.state == "slow_start":
            # 慢启动：cwnd指数增长
            self.cwnd += 1.0
            
            # 检查是否达到慢启动阈值
            if self.cwnd >= self.ssthresh:
                self.state = "congestion_avoidance"
                # 进入拥塞避免时，设置ack_count为当前cwnd的倒数
                self.ack_count = int(self.cwnd)
                
        elif self.state == "congestion_avoidance":
            # 拥塞避免：每RTT增加1个MSS
            # 实现方式：每收到ack_count个ACK，cwnd增加1
            self.ack_count -= 1
            if self.ack_count <= 0:
                self.cwnd += 1.0
                self.ack_count = int(self.cwnd)
    
    def _handle_duplicate_ack(self) -> None:
        """处理重复ACK"""
        if self.in_fast_recovery:
            # 快速恢复阶段：每个重复ACK增加cwnd
            self.cwnd += 1.0
        elif self.dup_acks == 3:
            # 收到3个重复ACK，触发快速重传
            self.on_loss("triple_duplicate")
    
    def _handle_new_ack_in_recovery(self, ack_number: int) -> None:
        """快速恢复阶段收到新ACK的处理"""
        if ack_number > self.recovery_point:
            # 新ACK超过了恢复点，退出快速恢复
            self.in_fast_recovery = False
            self.cwnd = self.ssthresh  # 设置cwnd为ssthresh
            self.state = "congestion_avoidance"
            self.ack_count = int(self.cwnd)
    
    def _handle_timeout(self) -> None:
        """处理超时丢包"""
        # 重置慢启动阈值
        self.ssthresh = max(2.0, self.cwnd / 2.0)
        
        # 重置拥塞窗口
        self.cwnd = 1.0
        
        # 重置状态
        self.state = "slow_start"
        self.in_fast_recovery = False
        self.dup_acks = 0
        
        # 记录丢包事件
        self.metrics.loss_rate += 1
    
    def _handle_triple_duplicate(self) -> None:
        """处理三个重复ACK（快速重传）"""
        # 设置慢启动阈值
        self.ssthresh = max(2.0, self.cwnd / 2.0)
        
        # 进入快速恢复
        self.in_fast_recovery = True
        self.recovery_point = self.last_ack
        
        # 设置cwnd为ssthresh + 3（因为已经收到3个重复ACK）
        self.cwnd = self.ssthresh + 3.0
        
        # 状态变为快速恢复
        self.state = "fast_recovery"
        
        # 记录丢包事件
        self.metrics.loss_rate += 1
    
    def reset(self) -> None:
        """重置算法状态"""
        super().reset()
        self.recovery_point = 0
        self.in_fast_recovery = False
        self.ack_count = 0
    
    def __str__(self) -> str:
        """返回算法状态字符串表示"""
        base_str = super().__str__()
        recovery_status = "in_recovery" if self.in_fast_recovery else "normal"
        return f"{base_str}, recovery={recovery_status}, dup_acks={self.dup_acks}"


# 示例：使用TCP Reno算法
if __name__ == "__main__":
    # 创建TCP Reno实例
    reno = TCPReno()
    
    print("初始状态:", reno)
    
    # 模拟收到ACK（慢启动阶段）
    for i in range(1, 6):
        reno.on_ack(i, rtt_sample=50.0)
        print(f"ACK {i}: {reno}")
    
    # 设置ssthresh为5，触发拥塞避免
    reno.ssthresh = 5.0
    
    # 继续收到ACK（拥塞避免阶段）
    for i in range(6, 11):
        reno.on_ack(i, rtt_sample=50.0)
        print(f"ACK {i}: {reno}")
    
    # 模拟丢包（超时）
    print("\n模拟超时丢包...")
    reno.on_loss("timeout")
    print("超时后:", reno)
    
    # 模拟三个重复ACK
    print("\n模拟三个重复ACK...")
    reno.on_ack(10, rtt_sample=50.0)  # 重复ACK 1
    reno.on_ack(10, rtt_sample=50.0)  # 重复ACK 2
    reno.on_ack(10, rtt_sample=50.0)  # 重复ACK 3
    print("快速重传后:", reno)
    
    # 获取性能指标
    metrics = reno.get_current_metrics()
    print(f"\n性能指标: 平均cwnd={metrics.avg_cwnd:.2f}, RTT={metrics.rtt:.1f}ms")
