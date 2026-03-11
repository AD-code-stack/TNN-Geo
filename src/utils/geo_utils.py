"""
地理位置相关工具函数
"""
import numpy as np
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    计算两个地理坐标之间的Haversine距离（公里）
    
    Args:
        lat1, lon1: 第一个点的纬度和经度
        lat2, lon2: 第二个点的纬度和经度
    
    Returns:
        距离（公里）
    """
    # 地球半径（公里）
    R = 6371.0
    
    # 转换为弧度
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    # Haversine公式
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c
    return distance


def calculate_centroid(locations: list) -> Tuple[float, float]:
    """
    计算一组位置的质心
    
    Args:
        locations: [(lat, lon), ...] 位置列表
    
    Returns:
        (lat, lon) 质心坐标
    """
    if not locations:
        return None, None
    
    lats = [loc[0] for loc in locations]
    lons = [loc[1] for loc in locations]
    
    return np.mean(lats), np.mean(lons)


def ip_to_int(ip: str) -> int:
    """
    将IP地址转换为整数
    
    Args:
        ip: IP地址字符串（如 "192.168.1.1"）
    
    Returns:
        整数表示的IP
    """
    parts = ip.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + \
           (int(parts[2]) << 8) + int(parts[3])


def int_to_ip(ip_int: int) -> str:
    """
    将整数转换为IP地址
    
    Args:
        ip_int: 整数表示的IP
    
    Returns:
        IP地址字符串
    """
    return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}." \
           f"{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"


def get_ip_range(ip: str, netmask: int = 24) -> Tuple[int, int]:
    """
    获取IP所在的网段范围
    
    Args:
        ip: IP地址字符串
        netmask: 网络掩码位数（默认24，即/24）
    
    Returns:
        (start_ip, end_ip) 网段的起始和结束IP（整数形式）
    """
    ip_int = ip_to_int(ip)
    
    # 计算网络掩码
    mask = (0xFFFFFFFF << (32 - netmask)) & 0xFFFFFFFF
    
    # 计算网络地址
    network = ip_int & mask
    
    # 计算广播地址
    broadcast = network | (~mask & 0xFFFFFFFF)
    
    return network, broadcast


def are_in_same_range(ip1: str, ip2: str, netmask: int = 24) -> bool:
    """
    判断两个IP是否在同一网段
    
    Args:
        ip1, ip2: IP地址字符串
        netmask: 网络掩码位数
    
    Returns:
        是否在同一网段
    """
    range1 = get_ip_range(ip1, netmask)
    range2 = get_ip_range(ip2, netmask)
    
    return range1 == range2
