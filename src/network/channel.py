"""
网络信道模型
模拟网络传输特性：带宽、延迟、丢包等
"""

import random
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PacketStatus(Enum):
    """数据包状态"""
    PENDING = "pending"      # 等待发送
    IN_TRANSIT = "in_transit"  # 传输中
    DELIVERED = "delivered"  # 已送达
    LOST = "lost"           # 丢失
    DELAYED = "delayed"     # 延迟


@dataclass
class Packet:
    """网络数据包"""
    packet_id: int           # 数据包ID
    seq_number: int          # 序列号
    size: int                # 数据包大小 (字节)
    send_time: float         # 发送时间
    receive_time: Optional[float] = None  # 接收时间
    status: PacketStatus = PacketStatus.PENDING  # 当前状态
    ack_number: Optional[int] = None  # ACK号（对于ACK包）
    is_ack: bool = False     # 是否是ACK包
    
    def __str__(self) -> str:
        packet_type = "ACK" if self.is_ack else "DATA"
        status_str = f", status={self.status.value}" if self.status != PacketStatus.PENDING else ""
        ack_str = f", ack={self.ack_number}" if self.ack_number is not None else ""
        return f"Packet[{self.packet_id}]({packet_type}, seq={self.seq_number}{ack_str}{status_str})"


class NetworkChannel:
    """
    网络信道模拟器
    
    模拟网络传输特性：
    1. 带宽限制
    2. 传输延迟
    3. 随机丢包
    4. 拥塞丢包
    5. 延迟变化
    """
    
    def __init__(self, 
                 bandwidth: float = 10.0,      # 带宽 (Mbps)
                 delay: float = 50.0,          # 基础延迟 (ms)
                 loss_probability: float = 0.0,  # 随机丢包概率
                 buffer_size: int = 100,       # 缓冲区大小 (数据包数)
                 jitter: float = 10.0,         # 延迟抖动 (ms)
                 mtu: int = 1500):             # 最大传输单元 (字节)
        """
        初始化网络信道
        
        Args:
            bandwidth: 带宽 (Mbps)
            delay: 基础延迟 (ms)
            loss_probability: 随机丢包概率 (0.0-1.0)
            buffer_size: 缓冲区大小
            jitter: 延迟抖动 (ms)
            mtu: 最大传输单元 (字节)
        """
        self.bandwidth = bandwidth  # Mbps
        self.base_delay = delay     # ms
        self.loss_probability = loss_probability
        self.buffer_size = buffer_size
        self.jitter = jitter
        self.mtu = mtu
        
        # 状态变量
        self.packets: Dict[int, Packet] = {}  # 所有数据包
        self.next_packet_id = 1
        self.buffer_occupancy = 0  # 当前缓冲区占用
        self.total_sent = 0        # 总发送数据包数
        self.total_lost = 0        # 总丢失数据包数
        self.total_delivered = 0   # 总送达数据包数
        
        # 性能统计
        self.start_time = time.time()
        self.throughput_history = []  # 吞吐量历史记录
        self.loss_rate_history = []   # 丢包率历史记录
        self.delay_history = []       # 延迟历史记录
        
        # 事件队列
        self.delivery_events = []  # (交付时间, 数据包ID)
    
    def send_packet(self, seq_number: int, size: int, is_ack: bool = False, 
                   ack_number: Optional[int] = None) -> Optional[Packet]:
        """
        发送数据包
        
        Args:
            seq_number: 序列号
            size: 数据包大小 (字节)
            is_ack: 是否是ACK包
            ack_number: ACK号（对于ACK包）
            
        Returns:
            发送的数据包，如果因缓冲区满而丢弃则返回None
        """
        # 检查缓冲区是否已满
        if self.buffer_occupancy >= self.buffer_size:
            self.total_lost += 1
            return None
        
        # 创建数据包
        packet_id = self.next_packet_id
        self.next_packet_id += 1
        
        packet = Packet(
            packet_id=packet_id,
            seq_number=seq_number,
            size=size,
            send_time=time.time(),
            is_ack=is_ack,
            ack_number=ack_number,
            status=PacketStatus.PENDING
        )
        
        # 检查是否随机丢包
        if random.random() < self.loss_probability:
            packet.status = PacketStatus.LOST
            self.total_lost += 1
            self.packets[packet_id] = packet
            return packet
        
        # 计算传输时间
        transmission_delay = self._calculate_transmission_delay(size)
        propagation_delay = self._calculate_propagation_delay()
        total_delay = transmission_delay + propagation_delay
        
        # 设置交付时间
        delivery_time = time.time() + total_delay
        packet.receive_time = delivery_time
        packet.status = PacketStatus.IN_TRANSIT
        
        # 添加到事件队列
        self.delivery_events.append((delivery_time, packet_id))
        self.delivery_events.sort(key=lambda x: x[0])  # 按时间排序
        
        # 更新状态
        self.packets[packet_id] = packet
        self.buffer_occupancy += 1
        self.total_sent += 1
        
        # 记录延迟
        self.delay_history.append((time.time(), total_delay * 1000))  # 转换为ms
        
        return packet
    
    def receive_packets(self) -> List[Packet]:
        """
        接收已到达的数据包
        
        Returns:
            已到达的数据包列表
        """
        current_time = time.time()
        delivered_packets = []
        
        # 检查所有等待交付的事件
        while self.delivery_events and self.delivery_events[0][0] <= current_time:
            delivery_time, packet_id = self.delivery_events.pop(0)
            
            if packet_id in self.packets:
                packet = self.packets[packet_id]
                packet.status = PacketStatus.DELIVERED
                packet.receive_time = delivery_time
                delivered_packets.append(packet)
                
                # 更新统计
                self.buffer_occupancy -= 1
                self.total_delivered += 1
        
        # 更新吞吐量统计
        self._update_throughput()
        
        return delivered_packets
    
    def _calculate_transmission_delay(self, size: int) -> float:
        """
        计算传输延迟
        
        Args:
            size: 数据包大小 (字节)
            
        Returns:
            传输延迟 (秒)
        """
        # 将带宽从Mbps转换为字节/秒
        bandwidth_bytes_per_sec = self.bandwidth * 1_000_000 / 8
        
        # 传输延迟 = 数据包大小 / 带宽
        return size / bandwidth_bytes_per_sec
    
    def _calculate_propagation_delay(self) -> float:
        """
        计算传播延迟（包含抖动）
        
        Returns:
            传播延迟 (秒)
        """
        # 基础延迟 + 随机抖动
        delay_ms = self.base_delay + random.uniform(-self.jitter, self.jitter)
        delay_ms = max(0, delay_ms)  # 确保非负
        
        return delay_ms / 1000.0  # 转换为秒
    
    def _update_throughput(self) -> None:
        """更新吞吐量统计"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed > 0:
            # 计算当前吞吐量 (Mbps)
            total_bytes_delivered = sum(
                p.size for p in self.packets.values() 
                if p.status == PacketStatus.DELIVERED
            )
            throughput_mbps = (total_bytes_delivered * 8) / (elapsed * 1_000_000)
            
            self.throughput_history.append((current_time, throughput_mbps))
            
            # 计算当前丢包率
            if self.total_sent > 0:
                loss_rate = self.total_lost / self.total_sent
                self.loss_rate_history.append((current_time, loss_rate))
    
    def get_channel_metrics(self) -> Dict[str, Any]:
        """
        获取信道性能指标
        
        Returns:
            信道性能指标字典
        """
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # 计算平均吞吐量
        avg_throughput = 0.0
        if self.throughput_history:
            avg_throughput = sum(t[1] for t in self.throughput_history) / len(self.throughput_history)
        
        # 计算平均丢包率
        avg_loss_rate = 0.0
        if self.loss_rate_history:
            avg_loss_rate = sum(l[1] for l in self.loss_rate_history) / len(self.loss_rate_history)
        
        # 计算平均延迟
        avg_delay = 0.0
        if self.delay_history:
            avg_delay = sum(d[1] for d in self.delay_history) / len(self.delay_history)
        
        return {
            "bandwidth_mbps": self.bandwidth,
            "base_delay_ms": self.base_delay,
            "current_buffer_occupancy": self.buffer_occupancy,
            "buffer_size": self.buffer_size,
            "total_sent": self.total_sent,
            "total_delivered": self.total_delivered,
            "total_lost": self.total_lost,
            "avg_throughput_mbps": avg_throughput,
            "avg_loss_rate": avg_loss_rate,
            "avg_delay_ms": avg_delay,
            "elapsed_time_sec": elapsed,
            "utilization": self.buffer_occupancy / self.buffer_size if self.buffer_size > 0 else 0.0
        }
    
    def reset(self) -> None:
        """重置信道状态"""
        self.packets.clear()
        self.next_packet_id = 1
        self.buffer_occupancy = 0
        self.total_sent = 0
        self.total_lost = 0
        self.total_delivered = 0
        self.throughput_history.clear()
        self.loss_rate_history.clear()
        self.delay_history.clear()
        self.delivery_events.clear()
        self.start_time = time.time()
    
    def set_network_conditions(self, 
                              bandwidth: Optional[float] = None,
                              delay: Optional[float] = None,
                              loss_probability: Optional[float] = None,
                              jitter: Optional[float] = None) -> None:
        """
        动态设置网络条件
        
        Args:
            bandwidth: 新带宽 (Mbps)
            delay: 新基础延迟 (ms)
            loss_probability: 新丢包概率
            jitter: 新延迟抖动 (ms)
        """
        if bandwidth is not None:
            self.bandwidth = bandwidth
        if delay is not None:
            self.base_delay = delay
        if loss_probability is not None:
            self.loss_probability = loss_probability
        if jitter is not None:
            self.jitter = jitter
    
    def __str__(self) -> str:
        """返回信道状态字符串表示"""
        metrics = self.get_channel_metrics()
        return (f"NetworkChannel: "
                f"BW={self.bandwidth}Mbps, "
                f"Delay={self.base_delay}ms, "
                f"Loss={self.loss_probability:.3f}, "
                f"Buffer={self.buffer_occupancy}/{self.buffer_size}, "
                f"Throughput={metrics['avg_throughput_mbps']:.2f}Mbps")


# 使用示例
if __name__ == "__main__":
    print("=== 网络信道模拟器演示 ===\n")
    
    # 创建网络信道
    channel = NetworkChannel(
        bandwidth=5.0,      # 5 Mbps
        delay=100.0,        # 100ms 延迟
        loss_probability=0.1,  # 10% 丢包率
        buffer_size=50,     # 50个数据包缓冲区
        jitter=20.0         # 20ms 抖动
    )
    
    print(f"初始信道: {channel}\n")
    
    # 模拟发送数据包
    print("发送数据包...")
    packets_sent = []
    for i in range(1, 11):
        packet = channel.send_packet(
            seq_number=i,
            size=1000,  # 1000字节
            is_ack=False
        )
        if packet:
            packets_sent.append(packet)
            print(f"  发送: {packet}")
        else:
            print(f"  丢弃: 序列号 {i} (缓冲区满)")
    
    print(f"\n发送了 {len(packets_sent)} 个数据包\n")
    
    # 等待一段时间让数据包传输
    print("等待传输...")
    time.sleep(0.5)
    
    # 接收数据包
    delivered = channel.receive_packets()
    print(f"接收到 {len(delivered)} 个数据包:")
    for packet in delivered:
        print(f"  接收: {packet}")
    
    # 获取信道指标
    print("\n信道性能指标:")
    metrics = channel.get_channel_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # 测试动态网络条件变化
    print("\n=== 动态网络条件变化测试 ===\n")
    print("增加带宽到10Mbps，减少延迟到50ms...")
    channel.set_network_conditions(bandwidth=10.0, delay=50.0)
    
    # 发送更多数据包
    for i in range(11, 16):
        channel.send_packet(seq_number=i, size=1000)
    
    time.sleep(0.3)
    delivered = channel.receive_packets()
    print(f"在新条件下接收到 {len(delivered)} 个数据包")
    print(f"最终信道状态: {channel}")
