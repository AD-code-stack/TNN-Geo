"""
位置传播器
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from ..utils.geo_utils import haversine_distance


class LocationPropagator:
    """位置传播器"""
    
    def __init__(self, max_iterations: int = 10, convergence_threshold: float = 0.01):
        """
        初始化传播器
        
        Args:
            max_iterations: 最大迭代次数
            convergence_threshold: 收敛阈值
        """
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        
        self.known_locations = {}  # 已知位置的IP
        self.propagated_locations = {}  # 传播得到的位置
    
    def initialize(self, interpolated_ips: Dict[str, Tuple[float, float]]):
        """
        初始化已知位置
        
        Args:
            interpolated_ips: 插值后的IP到位置映射
        """
        self.known_locations = interpolated_ips.copy()
    
    def propagate_via_neighbors(self, neighbor_pairs: List[Dict],
                                ip_ranges: Dict[str, Dict]) -> Dict[str, Tuple[float, float]]:
        """
        通过延迟邻居关系传播位置
        
        Args:
            neighbor_pairs: 延迟邻居对列表
            ip_ranges: IP范围信息（用于聚合层面的传播）
        
        Returns:
            新传播的IP位置
        """
        # 构建邻居图
        neighbor_graph = defaultdict(set)
        
        for pair in neighbor_pairs:
            ip1 = pair['ip1']
            ip2 = pair['ip2']
            
            neighbor_graph[ip1].add(ip2)
            neighbor_graph[ip2].add(ip1)
        
        # 迭代传播
        new_locations = {}
        
        for iteration in range(self.max_iterations):
            iteration_new = {}
            
            # 对于每个未知位置的IP
            for ip, neighbors in neighbor_graph.items():
                if ip in self.known_locations or ip in new_locations:
                    continue
                
                # 收集已知位置的邻居
                known_neighbors = []
                for neighbor in neighbors:
                    if neighbor in self.known_locations:
                        known_neighbors.append(self.known_locations[neighbor])
                    elif neighbor in new_locations:
                        known_neighbors.append(new_locations[neighbor])
                
                # 如果有已知邻居，使用其位置的平均值
                if known_neighbors:
                    lats = [loc[0] for loc in known_neighbors]
                    lons = [loc[1] for loc in known_neighbors]
                    
                    avg_lat = np.mean(lats)
                    avg_lon = np.mean(lons)
                    
                    iteration_new[ip] = (avg_lat, avg_lon)
            
            # 检查收敛
            if not iteration_new:
                break
            
            # 更新新位置
            new_locations.update(iteration_new)
            
            # 检查收敛率
            convergence_rate = len(iteration_new) / len(neighbor_graph)
            if convergence_rate < self.convergence_threshold:
                break
        
        self.propagated_locations = new_locations
        return new_locations
    
    def propagate_via_ranges(self, neighbor_pairs: List[Dict],
                            ip_to_range: Dict[str, str],
                            range_centers: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
        """
        在聚合层面（IP范围级别）使用延迟邻居传播位置
        
        Args:
            neighbor_pairs: 延迟邻居对列表
            ip_to_range: IP到范围ID的映射
            range_centers: 范围ID到中心位置的映射
        
        Returns:
            新传播的范围位置
        """
        # 构建范围级别的邻居图
        range_neighbors = defaultdict(set)
        
        for pair in neighbor_pairs:
            ip1 = pair['ip1']
            ip2 = pair['ip2']
            
            # 获取IP所属的范围
            range1 = ip_to_range.get(ip1)
            range2 = ip_to_range.get(ip2)
            
            if range1 and range2 and range1 != range2:
                range_neighbors[range1].add(range2)
                range_neighbors[range2].add(range1)
        
        # 传播位置到未知范围
        new_range_locations = {}
        
        for range_id, neighbors in range_neighbors.items():
            if range_id in range_centers:
                continue
            
            # 收集已知位置的邻居范围
            known_neighbor_locs = []
            for neighbor_range in neighbors:
                if neighbor_range in range_centers:
                    known_neighbor_locs.append(range_centers[neighbor_range])
            
            # 使用邻居位置的平均值
            if known_neighbor_locs:
                lats = [loc[0] for loc in known_neighbor_locs]
                lons = [loc[1] for loc in known_neighbor_locs]
                
                avg_lat = np.mean(lats)
                avg_lon = np.mean(lons)
                
                new_range_locations[range_id] = (avg_lat, avg_lon)
        
        return new_range_locations
    
    def get_all_locations(self) -> Dict[str, Tuple[float, float]]:
        """
        获取所有位置（已知+传播）
        
        Returns:
            所有IP到位置的映射
        """
        all_locations = self.known_locations.copy()
        all_locations.update(self.propagated_locations)
        return all_locations
    
    def evaluate_propagation(self, ground_truth: Dict[str, Tuple[float, float]]) -> Dict:
        """
        评估传播效果
        
        Args:
            ground_truth: 真实位置
        
        Returns:
            评估统计信息
        """
        errors = []
        
        for ip, pred_loc in self.propagated_locations.items():
            if ip in ground_truth:
                true_loc = ground_truth[ip]
                error = haversine_distance(
                    true_loc[0], true_loc[1],
                    pred_loc[0], pred_loc[1]
                )
                errors.append(error)
        
        if not errors:
            return {'error': 'No propagated IPs in ground truth'}
        
        # 计算不同距离阈值内的准确率
        thresholds = [5, 10, 20, 50]
        accuracy = {}
        for threshold in thresholds:
            within = sum(1 for e in errors if e <= threshold)
            accuracy[f'within_{threshold}km'] = within / len(errors)
        
        stats = {
            'total_propagated': len(self.propagated_locations),
            'evaluated': len(errors),
            'mean_error': np.mean(errors),
            'median_error': np.median(errors),
            'rmse': np.sqrt(np.mean([e**2 for e in errors])),
            **accuracy
        }
        
        return stats
    
    def save_propagated(self, output_path: str):
        """
        保存传播结果
        
        Args:
            output_path: 输出文件路径
        """
        data = []
        
        for ip, (lat, lon) in self.propagated_locations.items():
            data.append({
                'ip': ip,
                'latitude': lat,
                'longitude': lon,
                'source': 'propagated'
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    
    def save_all_locations(self, output_path: str):
        """
        保存所有位置（已知+传播）
        
        Args:
            output_path: 输出文件路径
        """
        data = []
        
        all_locations = self.get_all_locations()
        
        for ip, (lat, lon) in all_locations.items():
            source = 'known' if ip in self.known_locations else 'propagated'
            data.append({
                'ip': ip,
                'latitude': lat,
                'longitude': lon,
                'source': source
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
