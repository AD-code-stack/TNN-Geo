"""
Traceroute数据解析器
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
from collections import defaultdict


class TracerouteParser:
    """Traceroute数据解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.traceroutes = []
        self.rtt_cache = defaultdict(lambda: defaultdict(list))
    
    def parse_file(self, file_path: str) -> List[Dict]:
        """
        解析单个traceroute文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            解析后的traceroute列表
        """
        traceroutes = []
        
        # 这里需要根据实际的数据格式进行解析
        # 示例格式：源IP, 目标IP, 跳序列, RTT序列
        # 实际使用时需要根据CAIDA数据格式调整
        
        with open(file_path, 'r') as f:
            for line in f:
                # 跳过注释和空行
                if line.startswith('#') or not line.strip():
                    continue
                
                # 解析traceroute记录
                # 这里是示例代码，需要根据实际格式调整
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                
                traceroute = {
                    'source_ip': parts[0],
                    'dest_ip': parts[1],
                    'hops': [],
                    'rtts': []
                }
                
                # 解析跳和RTT
                for i in range(2, len(parts), 2):
                    if i + 1 < len(parts):
                        hop_ip = parts[i]
                        rtt = float(parts[i + 1])
                        traceroute['hops'].append(hop_ip)
                        traceroute['rtts'].append(rtt)
                
                traceroutes.append(traceroute)
        
        return traceroutes
    
    def parse_directory(self, dir_path: str) -> List[Dict]:
        """
        解析目录下的所有traceroute文件
        
        Args:
            dir_path: 目录路径
        
        Returns:
            所有解析后的traceroute列表
        """
        dir_path = Path(dir_path)
        all_traceroutes = []
        
        for file_path in dir_path.glob('*.txt'):
            traceroutes = self.parse_file(str(file_path))
            all_traceroutes.extend(traceroutes)
        
        self.traceroutes = all_traceroutes
        return all_traceroutes
    
    def aggregate_rtts(self, source_ip: str, target_ip: str) -> Dict[str, float]:
        """
        聚合从源IP到目标IP的多个traceroute实例的RTT
        使用中位数消除异常值
        
        Args:
            source_ip: 源IP
            target_ip: 目标IP
        
        Returns:
            {target_ip: median_rtt} 字典
        """
        # 收集所有从source_ip到target_ip的RTT
        rtts = []
        
        for tr in self.traceroutes:
            if tr['source_ip'] == source_ip:
                for i, hop_ip in enumerate(tr['hops']):
                    if hop_ip == target_ip:
                        rtts.append(tr['rtts'][i])
        
        if not rtts:
            return {}
        
        # 计算中位RTT
        median_rtt = np.median(rtts)
        
        # 计算RTT的变异系数（标准差/均值）
        # 如果变异系数过高，说明延迟不稳定，过滤掉
        if len(rtts) > 1:
            cv = np.std(rtts) / np.mean(rtts) if np.mean(rtts) > 0 else float('inf')
            if cv > 0.5:  # 变异系数阈值
                return {}
        
        return {target_ip: median_rtt}
    
    def extract_path_segments(self, min_instances: int = 3) -> List[Dict]:
        """
        从traceroute中提取路径段
        每个路径段包含源IP、两个连续的跳IP及其RTT
        
        Args:
            min_instances: 最少traceroute实例数
        
        Returns:
            路径段列表
        """
        segments = []
        
        # 按源IP和目标IP对分组traceroute
        grouped = defaultdict(list)
        for tr in self.traceroutes:
            key = (tr['source_ip'], tr['dest_ip'])
            grouped[key].append(tr)
        
        # 提取路径段
        for (source_ip, dest_ip), trs in grouped.items():
            if len(trs) < min_instances:
                continue
            
            # 对于每对连续的跳
            for tr in trs:
                for i in range(len(tr['hops']) - 1):
                    hop1 = tr['hops'][i]
                    hop2 = tr['hops'][i + 1]
                    rtt1 = tr['rtts'][i]
                    rtt2 = tr['rtts'][i + 1]
                    
                    segment = {
                        'source_ip': source_ip,
                        'hop1': hop1,
                        'hop2': hop2,
                        'rtt1': rtt1,
                        'rtt2': rtt2,
                        'latency_diff': abs(rtt2 - rtt1)
                    }
                    
                    segments.append(segment)
        
        return segments
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        将traceroute数据转换为DataFrame
        
        Returns:
            DataFrame
        """
        data = []
        
        for tr in self.traceroutes:
            for i, (hop, rtt) in enumerate(zip(tr['hops'], tr['rtts'])):
                data.append({
                    'source_ip': tr['source_ip'],
                    'dest_ip': tr['dest_ip'],
                    'hop_index': i,
                    'hop_ip': hop,
                    'rtt': rtt
                })
        
        return pd.DataFrame(data)
