"""
IP范围插值器
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from ..utils.geo_utils import (
    haversine_distance, calculate_centroid, 
    ip_to_int, int_to_ip, get_ip_range
)


class IPRangeInterpolator:
    """IP范围插值器"""
    
    def __init__(self, range_size: int = 256, min_ground_truth: int = 2,
                 max_distance_km: float = 25.0, netmask: int = 24):
        """
        初始化插值器
        
        Args:
            range_size: IP范围大小（默认256，即/24网段）
            min_ground_truth: 最少ground truth IP数量 - 参数n
            max_distance_km: 最大距离（公里）- 参数m
            netmask: 网络掩码位数
        """
        self.range_size = range_size
        self.min_ground_truth = min_ground_truth
        self.max_distance_km = max_distance_km
        self.netmask = netmask
        
        self.ip_ranges = {}  # {range_id: {center: (lat, lon), ips: [...]}}
        self.ip_to_range = {}  # {ip: range_id}
    
    def group_by_range(self, ground_truth: Dict[str, Tuple[float, float]]) -> Dict:
        """
        将ground truth IP按网段分组
        
        Args:
            ground_truth: IP到位置的映射
        
        Returns:
            按网段分组的字典 {range_id: [(ip, lat, lon), ...]}
        """
        ranges = defaultdict(list)
        
        for ip, (lat, lon) in ground_truth.items():
            # 获取IP所在的网段
            network, _ = get_ip_range(ip, self.netmask)
            range_id = int_to_ip(network)
            
            ranges[range_id].append((ip, lat, lon))
        
        return dict(ranges)
    
    def filter_valid_ranges(self, ranges: Dict) -> Dict:
        """
        过滤满足条件的IP范围
        条件：
        1. 至少包含n个ground truth IP
        2. 所有IP在m公里内
        
        Args:
            ranges: 按网段分组的字典
        
        Returns:
            过滤后的有效范围
        """
        valid_ranges = {}
        
        for range_id, ips_data in ranges.items():
            # 检查IP数量
            if len(ips_data) < self.min_ground_truth:
                continue
            
            # 提取位置
            locations = [(lat, lon) for _, lat, lon in ips_data]
            
            # 计算质心
            center_lat, center_lon = calculate_centroid(locations)
            
            # 检查所有IP是否在m公里内
            max_dist = 0
            for lat, lon in locations:
                dist = haversine_distance(center_lat, center_lon, lat, lon)
                max_dist = max(max_dist, dist)
            
            if max_dist <= self.max_distance_km:
                valid_ranges[range_id] = {
                    'center': (center_lat, center_lon),
                    'ips': [ip for ip, _, _ in ips_data],
                    'locations': locations,
                    'max_distance': max_dist,
                    'ip_count': len(ips_data)
                }
        
        self.ip_ranges = valid_ranges
        return valid_ranges
    
    def interpolate(self, ground_truth: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
        """
        执行IP范围插值
        
        Args:
            ground_truth: 原始ground truth IP到位置的映射
        
        Returns:
            扩展后的IP到位置映射（包含插值的IP）
        """
        # 按网段分组
        ranges = self.group_by_range(ground_truth)
        
        # 过滤有效范围
        valid_ranges = self.filter_valid_ranges(ranges)
        
        # 执行插值
        interpolated = {}
        
        for range_id, range_data in valid_ranges.items():
            center = range_data['center']
            
            # 获取该网段的所有IP
            network_int = ip_to_int(range_id)
            
            # 为该网段的所有IP分配质心位置
            for i in range(self.range_size):
                ip_int = network_int + i
                ip = int_to_ip(ip_int)
                
                # 跳过广播地址和网络地址
                if i == 0 or i == self.range_size - 1:
                    continue
                
                interpolated[ip] = center
                self.ip_to_range[ip] = range_id
        
        return interpolated
    
    def evaluate_interpolation(self, ground_truth: Dict[str, Tuple[float, float]],
                               interpolated: Dict[str, Tuple[float, float]]) -> Dict:
        """
        评估插值效果（使用交叉验证）
        
        Args:
            ground_truth: 原始ground truth
            interpolated: 插值结果
        
        Returns:
            评估统计信息
        """
        errors = []
        
        for ip, true_loc in ground_truth.items():
            if ip in interpolated:
                pred_loc = interpolated[ip]
                error = haversine_distance(
                    true_loc[0], true_loc[1],
                    pred_loc[0], pred_loc[1]
                )
                errors.append(error)
        
        if not errors:
            return {}
        
        # 计算不同距离阈值内的准确率
        thresholds = [10, 20, 30, 50]
        accuracy = {}
        for threshold in thresholds:
            within = sum(1 for e in errors if e <= threshold)
            accuracy[f'within_{threshold}km'] = within / len(errors)
        
        stats = {
            'total_evaluated': len(errors),
            'mean_error': np.mean(errors),
            'median_error': np.median(errors),
            'min_error': np.min(errors),
            'max_error': np.max(errors),
            'std_error': np.std(errors),
            **accuracy
        }
        
        return stats
    
    def get_coverage_expansion(self, original_size: int, interpolated_size: int) -> Dict:
        """
        计算覆盖率扩展
        
        Args:
            original_size: 原始ground truth大小
            interpolated_size: 插值后大小
        
        Returns:
            扩展统计信息
        """
        expansion_factor = interpolated_size / original_size if original_size > 0 else 0
        
        return {
            'original_size': original_size,
            'interpolated_size': interpolated_size,
            'expansion_factor': expansion_factor,
            'new_ips': interpolated_size - original_size
        }
    
    def save_ranges(self, output_path: str):
        """
        保存IP范围信息
        
        Args:
            output_path: 输出文件路径
        """
        data = []
        
        for range_id, range_data in self.ip_ranges.items():
            data.append({
                'range_id': range_id,
                'center_lat': range_data['center'][0],
                'center_lon': range_data['center'][1],
                'ip_count': range_data['ip_count'],
                'max_distance': range_data['max_distance']
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    
    def save_interpolated(self, interpolated: Dict[str, Tuple[float, float]], 
                         output_path: str):
        """
        保存插值结果
        
        Args:
            interpolated: 插值结果
            output_path: 输出文件路径
        """
        data = []
        
        for ip, (lat, lon) in interpolated.items():
            range_id = self.ip_to_range.get(ip, '')
            data.append({
                'ip': ip,
                'latitude': lat,
                'longitude': lon,
                'range_id': range_id
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
