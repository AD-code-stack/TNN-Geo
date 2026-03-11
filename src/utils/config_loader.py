"""
配置文件加载器
"""
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键（支持点号分隔的嵌套键，如 "latency_neighbors.high_accuracy.max_latency_diff"）
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_latency_neighbors_config(self, mode: str = "high_accuracy") -> Dict[str, Any]:
        """获取延迟邻居配置"""
        return self.config['latency_neighbors'][mode]
    
    def get_ip_range_config(self) -> Dict[str, Any]:
        """获取IP范围插值配置"""
        return self.config['ip_range_interpolation']
    
    def get_propagation_config(self) -> Dict[str, Any]:
        """获取位置传播配置"""
        return self.config['location_propagation']
    
    def get_data_paths(self) -> Dict[str, str]:
        """获取数据路径配置"""
        return self.config['data_paths']
    
    def get_evaluation_config(self) -> Dict[str, Any]:
        """获取评估配置"""
        return self.config['evaluation']
