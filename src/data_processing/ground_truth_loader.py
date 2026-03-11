"""
Ground Truth数据加载器
"""
import pandas as pd
from typing import Dict, Tuple, List
from pathlib import Path


class GroundTruthLoader:
    """Ground Truth数据加载器"""
    
    def __init__(self, file_path: str = None):
        """
        初始化加载器
        
        Args:
            file_path: Ground truth文件路径
        """
        self.file_path = file_path
        self.data = None
        self.ip_to_location = {}
        
        if file_path:
            self.load(file_path)
    
    def load(self, file_path: str) -> pd.DataFrame:
        """
        加载ground truth数据
        
        Args:
            file_path: 文件路径
        
        Returns:
            DataFrame
        """
        self.file_path = file_path
        
        # 读取CSV文件
        # 格式：IP地址, 纬度, 经度
        self.data = pd.read_csv(file_path)
        
        # 确保列名正确
        if 'ip' not in self.data.columns:
            # 尝试其他可能的列名
            possible_names = ['IP', 'ip_address', 'IP_address']
            for name in possible_names:
                if name in self.data.columns:
                    self.data.rename(columns={name: 'ip'}, inplace=True)
                    break
        
        if 'latitude' not in self.data.columns:
            possible_names = ['lat', 'Latitude', 'LAT']
            for name in possible_names:
                if name in self.data.columns:
                    self.data.rename(columns={name: 'latitude'}, inplace=True)
                    break
        
        if 'longitude' not in self.data.columns:
            possible_names = ['lon', 'lng', 'Longitude', 'LON']
            for name in possible_names:
                if name in self.data.columns:
                    self.data.rename(columns={name: 'longitude'}, inplace=True)
                    break
        
        # 构建IP到位置的映射
        self._build_ip_location_map()
        
        return self.data
    
    def _build_ip_location_map(self):
        """构建IP到位置的映射"""
        self.ip_to_location = {}
        
        for _, row in self.data.iterrows():
            ip = row['ip']
            lat = row['latitude']
            lon = row['longitude']
            self.ip_to_location[ip] = (lat, lon)
    
    def get_location(self, ip: str) -> Tuple[float, float]:
        """
        获取IP的位置
        
        Args:
            ip: IP地址
        
        Returns:
            (latitude, longitude) 或 (None, None)
        """
        return self.ip_to_location.get(ip, (None, None))
    
    def has_location(self, ip: str) -> bool:
        """
        检查IP是否有位置信息
        
        Args:
            ip: IP地址
        
        Returns:
            是否有位置信息
        """
        return ip in self.ip_to_location
    
    def get_ips(self) -> List[str]:
        """
        获取所有IP列表
        
        Returns:
            IP列表
        """
        return list(self.ip_to_location.keys())
    
    def filter_by_ips(self, ips: List[str]) -> pd.DataFrame:
        """
        根据IP列表过滤数据
        
        Args:
            ips: IP列表
        
        Returns:
            过滤后的DataFrame
        """
        return self.data[self.data['ip'].isin(ips)]
    
    def split_train_test(self, test_size: float = 0.1, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        划分训练集和测试集
        
        Args:
            test_size: 测试集比例
            random_state: 随机种子
        
        Returns:
            (train_df, test_df)
        """
        from sklearn.model_selection import train_test_split
        
        train_df, test_df = train_test_split(
            self.data,
            test_size=test_size,
            random_state=random_state
        )
        
        return train_df, test_df
    
    def get_statistics(self) -> Dict:
        """
        获取数据统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_ips': len(self.data),
            'unique_ips': self.data['ip'].nunique(),
            'lat_range': (self.data['latitude'].min(), self.data['latitude'].max()),
            'lon_range': (self.data['longitude'].min(), self.data['longitude'].max()),
        }
        
        return stats
    
    def save(self, output_path: str):
        """
        保存数据到文件
        
        Args:
            output_path: 输出文件路径
        """
        self.data.to_csv(output_path, index=False)
