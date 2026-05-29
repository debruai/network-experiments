"""
拥塞控制算法工厂
用于创建和管理不同的拥塞控制算法
"""

from typing import Dict, Any, Type
from .base import CongestionControl
from .reno import TCPReno
from .cubic import CUBIC


class AlgorithmFactory:
    """
    拥塞控制算法工厂
    
    支持创建以下算法：
    1. "reno": TCP Reno算法
    2. "cubic": CUBIC算法
    """
    
    # 支持的算法类型映射
    ALGORITHM_CLASSES = {
        "reno": TCPReno,
        "cubic": CUBIC,
    }
    
    # 算法默认参数
    DEFAULT_PARAMS = {
        "reno": {
            "mss": 1460,
            "initial_cwnd": 1,
        },
        "cubic": {
            "mss": 1460,
            "initial_cwnd": 1,
            "beta": 0.7,
            "C": 0.4,
        }
    }
    
    @classmethod
    def create_algorithm(cls, algorithm_type: str, **kwargs) -> CongestionControl:
        """
        创建拥塞控制算法实例
        
        Args:
            algorithm_type: 算法类型 ("reno" 或 "cubic")
            **kwargs: 算法特定参数
            
        Returns:
            拥塞控制算法实例
            
        Raises:
            ValueError: 如果算法类型不支持
        """
        if algorithm_type not in cls.ALGORITHM_CLASSES:
            supported = ", ".join(cls.ALGORITHM_CLASSES.keys())
            raise ValueError(f"不支持的算法类型: {algorithm_type}. 支持的算法: {supported}")
        
        # 获取默认参数并更新用户提供的参数
        params = cls.DEFAULT_PARAMS.get(algorithm_type, {}).copy()
        params.update(kwargs)
        
        # 创建算法实例
        algorithm_class = cls.ALGORITHM_CLASSES[algorithm_type]
        return algorithm_class(**params)
    
    @classmethod
    def get_supported_algorithms(cls) -> list:
        """
        获取支持的算法列表
        
        Returns:
            支持的算法类型列表
        """
        return list(cls.ALGORITHM_CLASSES.keys())
    
    @classmethod
    def get_algorithm_info(cls, algorithm_type: str) -> Dict[str, Any]:
        """
        获取算法信息
        
        Args:
            algorithm_type: 算法类型
            
        Returns:
            算法信息字典
        """
        if algorithm_type not in cls.ALGORITHM_CLASSES:
            raise ValueError(f"不支持的算法类型: {algorithm_type}")
        
        algorithm_class = cls.ALGORITHM_CLASSES[algorithm_type]
        
        info = {
            "name": algorithm_type,
            "class": algorithm_class.__name__,
            "description": algorithm_class.__doc__.strip().split('\n')[0] if algorithm_class.__doc__ else "",
            "default_params": cls.DEFAULT_PARAMS.get(algorithm_type, {}),
        }
        
        # 添加算法特定信息
        if algorithm_type == "reno":
            info.update({
                "features": [
                    "慢启动 (Slow Start)",
                    "拥塞避免 (Congestion Avoidance)",
                    "快速重传 (Fast Retransmit)",
                    "快速恢复 (Fast Recovery)"
                ],
                "suitable_for": ["传统网络", "低带宽网络", "教学示例"]
            })
        elif algorithm_type == "cubic":
            info.update({
                "features": [
                    "立方增长函数",
                    "RTT公平性",
                    "快速收敛优化",
                    "TCP友好模式"
                ],
                "suitable_for": ["高速网络", "高带宽延迟积网络", "现代互联网"]
            })
        
        return info
    
    @classmethod
    def create_comparison_group(cls, algorithm_types=None, **common_params):
        """
        创建算法比较组
        
        Args:
            algorithm_types: 要比较的算法类型列表，如果为None则使用所有支持的算法
            **common_params: 所有算法共享的参数
            
        Returns:
            算法实例字典 {算法类型: 算法实例}
        """
        if algorithm_types is None:
            algorithm_types = cls.get_supported_algorithms()
        
        algorithms = {}
        for algo_type in algorithm_types:
            try:
                algorithms[algo_type] = cls.create_algorithm(algo_type, **common_params)
            except ValueError as e:
                print(f"警告: 无法创建算法 {algo_type}: {e}")
        
        return algorithms


# 使用示例
if __name__ == "__main__":
    print("=== 拥塞控制算法工厂演示 ===\n")
    
    # 1. 获取支持的算法
    supported = AlgorithmFactory.get_supported_algorithms()
    print(f"支持的算法: {supported}\n")
    
    # 2. 获取算法信息
    for algo in supported:
        info = AlgorithmFactory.get_algorithm_info(algo)
        print(f"算法: {info['name']}")
        print(f"描述: {info['description']}")
        print(f"默认参数: {info['default_params']}")
        if 'features' in info:
            print(f"特性: {', '.join(info['features'])}")
        if 'suitable_for' in info:
            print(f"适用场景: {', '.join(info['suitable_for'])}")
        print()
    
    # 3. 创建算法实例
    print("=== 创建算法实例 ===\n")
    
    # 创建TCP Reno
    reno = AlgorithmFactory.create_algorithm("reno", initial_cwnd=2)
    print(f"创建TCP Reno: {reno}\n")
    
    # 创建CUBIC
    cubic = AlgorithmFactory.create_algorithm("cubic", beta=0.8, C=0.3)
    print(f"创建CUBIC: {cubic}")
    print(f"CUBIC参数: {cubic.get_parameters() if hasattr(cubic, 'get_parameters') else 'N/A'}\n")
    
    # 4. 创建比较组
    print("=== 创建算法比较组 ===\n")
    comparison_group = AlgorithmFactory.create_comparison_group(
        algorithm_types=["reno", "cubic"],
        mss=1460,
        initial_cwnd=1
    )
    
    for algo_name, algo_instance in comparison_group.items():
        print(f"{algo_name}: {algo_instance}")
    
    # 5. 测试错误情况
    print("\n=== 测试错误处理 ===\n")
    try:
        unknown = AlgorithmFactory.create_algorithm("unknown")
    except ValueError as e:
        print(f"预期错误: {e}")
