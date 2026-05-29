"""
网络模拟器
整合拥塞控制算法和网络信道，进行端到端模拟
"""

import time
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..algorithms.factory import AlgorithmFactory
from .channel import NetworkChannel, Packet, PacketStatus


class SimulationEvent(Enum):
    """模拟事件类型"""
    PACKET_SENT = "packet_sent"
    PACKET_DELIVERED = "packet_delivered"
    PACKET_LOST = "packet_lost"
    ACK_SENT = "ack_sent"
    ACK_DELIVERED = "ack_delivered"
    ACK_LOST = "ack_lost"
    CWND_UPDATE = "cwnd_update"
    STATE_CHANGE = "state_change"
    LOSS_DETECTED = "loss_detected"


@dataclass
class SimulationMetrics:
    """模拟性能指标"""
    total_packets_sent: int = 0
    total_packets_delivered: int = 0
    total_packets_lost: int = 0
    total_acks_sent: int = 0
    total_acks_delivered: int = 0
    total_acks_lost: int = 0
    total_bytes_sent: int = 0
    total_bytes_delivered: int = 0
    simulation_time: float = 0.0
    throughput_mbps: float = 0.0
    goodput_mbps: float = 0.0
    loss_rate: float = 0.0
    avg_cwnd: float = 0.0
    avg_rtt: float = 0.0
    fairness_index: float = 0.0


class NetworkSimulator:
    """
    网络模拟器
    
    模拟端到端网络传输，包括：
    1. 发送方：使用拥塞控制算法控制发送速率
    2. 接收方：发送ACK确认
    3. 网络信道：模拟传输特性
    """
    
    def __init__(self, 
                 algorithm_type: str = "reno",
                 bandwidth: float = 10.0,
                 delay: float = 50.0,
                 loss_probability: float = 0.0,
                 simulation_duration: float = 30.0,
                 mss: int = 1460,
                 **algorithm_params):
        """
        初始化网络模拟器
        
        Args:
            algorithm_type: 拥塞控制算法类型 ("reno" 或 "cubic")
            bandwidth: 网络带宽 (Mbps)
            delay: 网络延迟 (ms)
            loss_probability: 丢包概率
            simulation_duration: 模拟持续时间 (秒)
            mss: 最大报文段大小 (字节)
            **algorithm_params: 算法特定参数
        """
        # 创建拥塞控制算法
        self.algorithm = AlgorithmFactory.create_algorithm(
            algorithm_type, 
            mss=mss,
            **algorithm_params
        )
        
        # 创建网络信道（双向）
        self.forward_channel = NetworkChannel(
            bandwidth=bandwidth,
            delay=delay / 2,  # 单向延迟
            loss_probability=loss_probability,
            buffer_size=100,
            jitter=10.0,
            mtu=1500
        )
        
        self.reverse_channel = NetworkChannel(
            bandwidth=bandwidth,
            delay=delay / 2,  # 单向延迟
            loss_probability=loss_probability,
            buffer_size=100,
            jitter=10.0,
            mtu=1500
        )
        
        # 模拟参数
        self.simulation_duration = simulation_duration
        self.mss = mss
        
        # 状态变量
        self.next_seq_number = 1
        self.next_ack_number = 0
        self.last_ack_received = 0
        self.unacked_packets: Dict[int, Packet] = {}  # 未确认的数据包
        self.pending_acks: Dict[int, Packet] = {}     # 等待发送的ACK
        
        # 事件记录
        self.events: List[Tuple[float, SimulationEvent, Any]] = []
        self.metrics = SimulationMetrics()
        
        # 时间管理
        self.start_time = 0.0
        self.current_time = 0.0
        self.is_running = False
        
        # 性能历史记录
        self.cwnd_history: List[Tuple[float, float]] = []
        self.rtt_history: List[Tuple[float, float]] = []
        self.throughput_history: List[Tuple[float, float]] = []
    
    def run(self) -> SimulationMetrics:
        """
        运行模拟
        
        Returns:
            模拟性能指标
        """
        self.start_time = time.time()
        self.current_time = 0.0
        self.is_running = True
        
        print(f"开始模拟: {self.algorithm.__class__.__name__}")
        print(f"网络条件: {self.forward_channel}")
        print(f"模拟时长: {self.simulation_duration}秒")
        print("-" * 50)
        
        # 主模拟循环
        while self.current_time < self.simulation_duration and self.is_running:
            self._update_time()
            self._process_events()
            self._send_packets()
            self._send_acks()
            self._receive_packets()
            self._receive_acks()
            
            # 短暂休眠以避免CPU过度使用
            time.sleep(0.001)
        
        # 计算最终指标
        self._calculate_final_metrics()
        
        print(f"\n模拟完成!")
        print(f"总发送数据包: {self.metrics.total_packets_sent}")
        print(f"总送达数据包: {self.metrics.total_packets_delivered}")
        print(f"总丢失数据包: {self.metrics.total_packets_lost}")
        print(f"吞吐量: {self.metrics.throughput_mbps:.2f} Mbps")
        print(f"丢包率: {self.metrics.loss_rate:.2%}")
        print(f"平均拥塞窗口: {self.metrics.avg_cwnd:.2f} MSS")
        
        return self.metrics
    
    def _update_time(self) -> None:
        """更新当前时间"""
        self.current_time = time.time() - self.start_time
    
    def _process_events(self) -> None:
        """处理待处理事件"""
        # 处理前向信道的数据包
        delivered_packets = self.forward_channel.receive_packets()
        for packet in delivered_packets:
            if packet.status == PacketStatus.DELIVERED:
                self._handle_packet_delivered(packet)
            elif packet.status == PacketStatus.LOST:
                self._handle_packet_lost(packet)
        
        # 处理反向信道的ACK
        delivered_acks = self.reverse_channel.receive_packets()
        for ack in delivered_acks:
            if ack.status == PacketStatus.DELIVERED:
                self._handle_ack_delivered(ack)
            elif ack.status == PacketStatus.LOST:
                self._handle_ack_lost(ack)
    
    def _send_packets(self) -> None:
        """根据拥塞控制算法发送数据包"""
        # 计算可以发送的数据包数量
        window_size = int(self.algorithm.cwnd)
        in_flight = len(self.unacked_packets)
        available_window = max(0, window_size - in_flight)
        
        # 发送数据包
        for _ in range(available_window):
            self._send_single_packet()
    
    def _send_single_packet(self) -> None:
        """发送单个数据包"""
        seq_number = self.next_seq_number
        self.next_seq_number += 1
        
        # 发送数据包
        packet = self.forward_channel.send_packet(
            seq_number=seq_number,
            size=self.mss,
            is_ack=False
        )
        
        if packet:
            # 记录发送事件
            self.unacked_packets[seq_number] = packet
            self.metrics.total_packets_sent += 1
            self.metrics.total_bytes_sent += self.mss
            
            self.events.append((self.current_time, SimulationEvent.PACKET_SENT, {
                "seq_number": seq_number,
                "cwnd": self.algorithm.cwnd
            }))
            
            # 记录cwnd历史
            self.cwnd_history.append((self.current_time, self.algorithm.cwnd))
        else:
            # 数据包被丢弃（缓冲区满）
            self.metrics.total_packets_lost += 1
            
            self.events.append((self.current_time, SimulationEvent.PACKET_LOST, {
                "seq_number": seq_number,
                "reason": "buffer_full"
            }))
    
    def _send_acks(self) -> None:
        """发送ACK确认"""
        # 检查是否有待发送的ACK
        if self.next_ack_number > self.last_ack_received:
            ack_number = self.next_ack_number
            
            # 发送ACK
            ack = self.reverse_channel.send_packet(
                seq_number=0,  # ACK没有序列号
                size=40,       # TCP ACK大小约40字节
                is_ack=True,
                ack_number=ack_number
            )
            
            if ack:
                self.pending_acks[ack_number] = ack
                self.metrics.total_acks_sent += 1
                
                self.events.append((self.current_time, SimulationEvent.ACK_SENT, {
                    "ack_number": ack_number
                }))
    
    def _receive_packets(self) -> None:
        """接收数据包（接收方逻辑）"""
        # 在实际实现中，这里会处理接收到的数据包
        # 对于模拟，我们假设接收方总是能正确接收并生成ACK
        pass
    
    def _receive_acks(self) -> None:
        """接收ACK（发送方逻辑）"""
        # ACK接收在_process_events中处理
        pass
    
    def _handle_packet_delivered(self, packet: Packet) -> None:
        """处理数据包送达事件"""
        self.metrics.total_packets_delivered += 1
        self.metrics.total_bytes_delivered += packet.size
        
        # 更新下一个期望的ACK号
        if packet.seq_number >= self.next_ack_number:
            self.next_ack_number = packet.seq_number + 1
        
        self.events.append((self.current_time, SimulationEvent.PACKET_DELIVERED, {
            "seq_number": packet.seq_number,
            "delivery_time": packet.receive_time
        }))
    
    def _handle_packet_lost(self, packet: Packet) -> None:
        """处理数据包丢失事件"""
        self.metrics.total_packets_lost += 1
        
        # 从未确认列表中移除
        if packet.seq_number in self.unacked_packets:
            del self.unacked_packets[packet.seq_number]
        
        self.events.append((self.current_time, SimulationEvent.PACKET_LOST, {
            "seq_number": packet.seq_number,
            "reason": "random_loss"
        }))
    
    def _handle_ack_delivered(self, ack: Packet) -> None:
        """处理ACK送达事件"""
        if ack.ack_number is None:
            return
        
        ack_number = ack.ack_number
        self.metrics.total_acks_delivered += 1
        
        # 从待处理ACK列表中移除
        if ack_number in self.pending_acks:
            del self.pending_acks[ack_number]
        
        # 从未确认数据包列表中移除已确认的数据包
        seq_to_remove = []
        for seq in self.unacked_packets:
            if seq < ack_number:
                seq_to_remove.append(seq)
        
        for seq in seq_to_remove:
            del self.unacked_packets[seq]
        
        # 更新最后接收到的ACK
        self.last_ack_received = max(self.last_ack_received, ack_number)
        
        # 计算RTT样本
        if ack_number in self.unacked_packets:
            # 理论上不应该发生，但安全处理
            pass
        
        # 通知拥塞控制算法
        rtt_sample = None
        if ack.receive_time and ack.send_time:
            rtt_sample = (ack.receive_time - ack.send_time) * 1000  # 转换为ms
        
        self.algorithm.on_ack(ack_number, rtt_sample)
        
        # 记录事件
        self.events.append((self.current_time, SimulationEvent.ACK_DELIVERED, {
            "ack_number": ack_number,
            "rtt_sample": rtt_sample
        }))
        
        # 记录RTT历史
        if rtt_sample:
            self.rtt_history.append((self.current_time, rtt_sample))
    
    def _handle_ack_lost(self, ack: Packet) -> None:
        """处理ACK丢失事件"""
        self.metrics.total_acks_lost += 1
        
        self.events.append((self.current_time, SimulationEvent.ACK_LOST, {
            "ack_number": ack.ack_number if ack.ack_number else "unknown"
        }))
    
    def _calculate_final_metrics(self) -> None:
        """计算最终性能指标"""
        # 计算吞吐量
        if self.current_time > 0:
            self.metrics.throughput_mbps = (
                self.metrics.total_bytes_delivered * 8 / 
                (self.current_time * 1_000_000)
            )
            
            # 计算有效吞吐量（goodput）
            self.metrics.goodput_mbps = (
                self.metrics.total_bytes_delivered * 8 / 
                (self.current_time * 1_000_000)
            )
        
        # 计算丢包率
        total_packets = self.metrics.total_packets_sent
        if total_packets > 0:
            self.metrics.loss_rate = self.metrics.total_packets_lost / total_packets
        
        # 计算平均拥塞窗口
        if self.cwnd_history:
            times, cwnds = zip(*self.cwnd_history)
            self.metrics.avg_cwnd = sum(cwnds) / len(cwnds)
        
        # 计算平均RTT
        if self.rtt_history:
            times, rtts = zip(*self.rtt_history)
            self.metrics.avg_rtt = sum(rtts) / len(rtts)
        
        # 模拟时间
        self.metrics.simulation_time = self.current_time
    
    def get_event_log(self, event_type: Optional[SimulationEvent] = None) -> List[Tuple[float, SimulationEvent, Any]]:
        """
        获取事件日志
        
        Args:
            event_type: 过滤事件类型
            
        Returns:
            事件日志列表
        """
        if event_type:
            return [event for event in self.events if event[1] == event_type]
        return self.events
    
    def get_algorithm_state(self) -> Dict[str, Any]:
        """获取算法当前状态"""
        return {
            "algorithm": self.algorithm.__class__.__name__,
            "cwnd": self.algorithm.cwnd,
            "ssthresh": self.algorithm.ssthresh,
            "state": self.algorithm.state,
            "rtt": self.algorithm.rtt,
        }
    
    def reset(self) -> None:
        """重置模拟器"""
        self.algorithm.reset()
        self.forward_channel.reset()
        self.reverse_channel.reset()
        
        self.next_seq_number = 1
        self.next_ack_number = 0
        self.last_ack_received = 0
        self.unacked_packets.clear()
        self.pending_acks.clear()
        
        self.events.clear()
        self.metrics = SimulationMetrics()
        self.cwnd_history.clear()
        self.rtt_history.clear()
        self.throughput_history.clear()
        
        self.start_time = 0.0
        self.current_time = 0.0
        self.is_running = False
    
    def __str__(self) -> str:
        """返回模拟器状态字符串表示"""
        return (f"NetworkSimulator[{self.algorithm.__class__.__name__}]: "
                f"time={self.current_time:.1f}s, "
                f"cwnd={self.algorithm.cwnd:.1f}, "
                f"sent={self.metrics.total_packets_sent}, "
                f"delivered={self.metrics.total_packets_delivered}")


# 使用示例
if __name__ == "__main__":
    print("=== 网络模拟器演示 ===\n")
    
    # 测试TCP Reno
    print("测试TCP Reno算法...")
    reno_simulator = NetworkSimulator(
        algorithm_type="reno",
        bandwidth=5.0,
        delay=100.0,
        loss_probability=0.05,  # 5%丢包率
        simulation_duration=10.0
    )
    
    reno_metrics = reno_simulator.run()
    
    print("\n" + "="*50 + "\n")
    
    # 测试CUBIC
    print("测试CUBIC算法...")
    cubic_simulator = NetworkSimulator(
        algorithm_type="cubic",
        bandwidth=5.0,
        delay=100.0,
        loss_probability=0.05,  # 5%丢包率
        simulation_duration=10.0,
        beta=0.7,
        C=0.4
    )
    
    cubic_metrics = cubic_simulator.run()
    
    # 对比结果
    print("\n" + "="*50)
    print("算法对比结果:")
    print("="*50)
    
    print(f"{'指标':<20} {'TCP Reno':<15} {'CUBIC':<15} {'差异':<10}")
    print("-" * 60)
    
    metrics_to_compare = [
        ("吞吐量 (Mbps)", "throughput_mbps", "{:.2f}"),
        ("丢包率", "loss_rate", "{:.2%}"),
        ("平均cwnd", "avg_cwnd", "{:.2f}"),
        ("平均RTT (ms)", "avg_rtt", "{:.1f}"),
        ("发送数据包", "total_packets_sent", "{:d}"),
        ("送达数据包", "total_packets_delivered", "{:d}"),
    ]
    
    for name, attr, fmt in metrics_to_compare:
        reno_value = getattr(reno_metrics, attr)
        cubic_value = getattr(cubic_metrics, attr)
        
        if isinstance(reno_value, float):
            diff = cubic_value - reno_value
            diff_str = f"{diff:+.2f}"
        else:
            diff = cubic_value - reno_value
            diff_str = f"{diff:+d}"
        
        print(f"{name:<20} {fmt.format(reno_value):<15} {fmt.format(cubic_value):<15} {diff_str:<10}")
