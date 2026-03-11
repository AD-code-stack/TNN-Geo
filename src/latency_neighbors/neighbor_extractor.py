"""
延迟邻居提取器
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set
from collections import defaultdict
from ..utils.geo_utils import haversine_distance


class LatencyNeighborExtractor:
    """延迟邻居提取器"""
    
    def __init__(self, max_latency_diff: float = 2.0, max_rtt: float = 2.0,
                 use_median: bool = True, min_instances: int = 3):
        """
        初始化提取器
        
        Args:
            max_latency_diff: 最大延迟差（毫秒）- 参数X
            max_rtt: 最大RTT（毫秒）- 参数Y
            use_median: 是否使用中位RTT
            min_instances: 最少traceroute实例数
        """
        self.max_latency_diff = max_latency_diff
        self.max_rtt = max_rtt
        self.use_median = use_median
        self.min_instances = min_instances
        
        self.neighbor_pairs = []
        self.rtt_aggregated = defaultdict(lambda: defaultdict(list))
    
    def aggregate_rtts(self, traceroutes: List[Dict]) -> Dict:
        """
        聚合多个traceroute实例的RTT，使用中位数消除异常值
        
        Args:
            traceroutes: traceroute列表
        
        Returns:
            聚合后的RTT字典 {(source_ip, hop_ip): median_rtt}
        """
        # 收集所有RTT
        rtt_collection = defaultdict(list)
        
        for tr in traceroutes:
            source_ip = tr['source_ip']
            for hop_ip, rtt in zip(tr['hops'], tr['rtts']):
                key = (source_ip, hop_ip)
                rtt_collection[key].append(rtt)
        
        # 计算中位RTT
        aggregated = {}
        for key, rtts in rtt_collection.items():
            if len(rtts) >= self.min_instances:
                if self.use_median:
                    aggregated[key] = np.median(rtts)
                else:
                    aggregated[key] = np.mean(rtts)
                
                # 过滤变异系数过高的 (放宽阈值到1.0,允许更多变异)
                if len(rtts) > 1:
                    cv = np.std(rtts) / np.mean(rtts) if np.mean(rtts) > 0 else float('inf')
                    if cv > 1.0:  # 放宽阈值:从0.5改为1.0
                        del aggregated[key]
        
        self.rtt_aggregated = aggregated
        return aggregated
    
    def extract_neighbors(self, traceroutes: List[Dict], 
                         ground_truth: Dict[str, Tuple[float, float]] = None) -> List[Dict]:
        """
        提取延迟邻居对
        
        Args:
            traceroutes: traceroute列表
            ground_truth: IP到位置的映射（可选，用于验证）
        
        Returns:
            邻居对列表
        """
        # 首先聚合RTT
        aggregated_rtts = self.aggregate_rtts(traceroutes)
        
        # 按源IP分组
        by_source = defaultdict(list)
        for (source_ip, hop_ip), rtt in aggregated_rtts.items():
            by_source[source_ip].append((hop_ip, rtt))
        
        # 第1步: 提取原始邻居对
        raw_pairs = []
        
        for source_ip, hops in by_source.items():
            # 对于每对跳
            for i in range(len(hops)):
                for j in range(i + 1, len(hops)):
                    hop1, rtt1 = hops[i]
                    hop2, rtt2 = hops[j]
                    
                    # 计算延迟差（RTT差值）
                    latency_diff = abs(rtt2 - rtt1)  # 直接使用RTT差值,不需要除以2
                    
                    # 检查是否满足条件
                    if latency_diff <= self.max_latency_diff:
                        # 检查RTT是否在阈值内
                        if rtt1 <= self.max_rtt and rtt2 <= self.max_rtt:
                            pair = {
                                'source_ip': source_ip,
                                'ip1': hop1,
                                'ip2': hop2,
                                'rtt1': rtt1,
                                'rtt2': rtt2,
                                'latency_diff': latency_diff
                            }
                            raw_pairs.append(pair)
        
        # 第2步: 聚合同一IP对在多个traceroute中的出现
        neighbor_pairs = self._aggregate_neighbor_pairs(raw_pairs, ground_truth)
        
        self.neighbor_pairs = neighbor_pairs
        return neighbor_pairs
    
    def _aggregate_neighbor_pairs(self, raw_pairs: List[Dict],
                                  ground_truth: Dict[str, Tuple[float, float]] = None) -> List[Dict]:
        """
        聚合同一IP对在多个traceroute中的出现
        
        Args:
            raw_pairs: 原始邻居对列表
            ground_truth: IP到位置的映射（可选）
        
        Returns:
            聚合后的邻居对列表
        """
        # 按IP对分组
        pairs_by_ips = defaultdict(list)
        
        for pair in raw_pairs:
            # 使用排序的IP对作为key,确保(A,B)和(B,A)被视为同一对
            ip1, ip2 = pair['ip1'], pair['ip2']
            key = tuple(sorted([ip1, ip2]))
            pairs_by_ips[key].append(pair)
        
        # 聚合每个IP对
        aggregated_pairs = []
        
        for (ip1, ip2), pairs in pairs_by_ips.items():
            # 收集所有延迟差
            latency_diffs = [p['latency_diff'] for p in pairs]
            
            # 计算中位延迟差
            median_latency_diff = np.median(latency_diffs)
            
            # 过滤变异系数过高的对
            if len(latency_diffs) > 1:
                cv = np.std(latency_diffs) / np.mean(latency_diffs) if np.mean(latency_diffs) > 0 else float('inf')
                if cv > 1.0:  # 变异系数阈值
                    continue  # 跳过这个对
            
            # 创建聚合后的邻居对
            aggregated_pair = {
                'ip1': ip1,
                'ip2': ip2,
                'latency_diff': median_latency_diff,
                'instances': len(pairs),  # 出现次数
                'mean_latency_diff': np.mean(latency_diffs),
                'std_latency_diff': np.std(latency_diffs) if len(latency_diffs) > 1 else 0
            }
            
            # 如果有ground truth，计算实际距离
            if ground_truth:
                if ip1 in ground_truth and ip2 in ground_truth:
                    loc1 = ground_truth[ip1]
                    loc2 = ground_truth[ip2]
                    distance = haversine_distance(
                        loc1[0], loc1[1], loc2[0], loc2[1]
                    )
                    aggregated_pair['actual_distance'] = distance
            
            aggregated_pairs.append(aggregated_pair)
        
        return aggregated_pairs
    
    def validate_neighbors(self, distance_threshold: float = 10.0) -> Dict:
        """
        验证邻居对的准确性
        需要neighbor_pairs中包含actual_distance字段
        
        Args:
            distance_threshold: 距离阈值（公里）
        
        Returns:
            验证统计信息
        """
        if not self.neighbor_pairs:
            return {}
        
        # 过滤有实际距离的邻居对
        pairs_with_distance = [p for p in self.neighbor_pairs if 'actual_distance' in p]
        
        if not pairs_with_distance:
            return {'error': 'No pairs with actual distance'}
        
        # 计算在阈值内的比例
        within_threshold = sum(1 for p in pairs_with_distance 
                              if p['actual_distance'] <= distance_threshold)
        
        total = len(pairs_with_distance)
        accuracy = within_threshold / total if total > 0 else 0
        
        # 计算距离统计
        distances = [p['actual_distance'] for p in pairs_with_distance]
        
        stats = {
            'total_pairs': total,
            'within_threshold': within_threshold,
            'accuracy': accuracy,
            'mean_distance': np.mean(distances),
            'median_distance': np.median(distances),
            'min_distance': np.min(distances),
            'max_distance': np.max(distances)
        }
        
        return stats
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        将邻居对转换为DataFrame
        
        Returns:
            DataFrame
        """
        return pd.DataFrame(self.neighbor_pairs)
    
    def save(self, output_path: str):
        """
        保存邻居对到文件
        
        Args:
            output_path: 输出文件路径
        """
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
