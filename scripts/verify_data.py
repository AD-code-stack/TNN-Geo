"""
数据验证脚本
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from utils.geo_utils import haversine_distance, get_ip_range


def verify_ground_truth(file_path: str):
    """验证Ground Truth数据"""
    print("\n" + "="*60)
    print("Ground Truth数据验证")
    print("="*60)
    
    df = pd.read_csv(file_path)
    
    print(f"\n基本统计:")
    print(f"  总IP数: {len(df)}")
    print(f"  唯一IP数: {df['ip'].nunique()}")
    print(f"  纬度范围: {df['latitude'].min():.2f}° - {df['latitude'].max():.2f}°")
    print(f"  经度范围: {df['longitude'].min():.2f}° - {df['longitude'].max():.2f}°")
    
    # 统计/24网段
    ranges = {}
    for _, row in df.iterrows():
        network, _ = get_ip_range(row['ip'], 24)
        if network not in ranges:
            ranges[network] = []
        ranges[network].append((row['latitude'], row['longitude']))
    
    print(f"\nIP范围统计:")
    print(f"  /24网段数: {len(ranges)}")
    print(f"  平均每网段IP数: {len(df) / len(ranges):.1f}")
    
    # 检查每个网段的地理分布
    max_distances = []
    for network, locations in ranges.items():
        if len(locations) < 2:
            continue
        
        # 计算质心
        lats = [loc[0] for loc in locations]
        lons = [loc[1] for loc in locations]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        # 计算最大距离
        max_dist = 0
        for lat, lon in locations:
            dist = haversine_distance(center_lat, center_lon, lat, lon)
            max_dist = max(max_dist, dist)
        
        max_distances.append(max_dist)
    
    print(f"\n网段地理分布:")
    print(f"  平均最大距离: {sum(max_distances) / len(max_distances):.2f} km")
    print(f"  最大距离范围: {min(max_distances):.2f} - {max(max_distances):.2f} km")
    print(f"  符合m=25km的网段: {sum(1 for d in max_distances if d <= 25)} / {len(max_distances)}")
    
    return df


def verify_traceroute(file_path: str, gt_ips: set):
    """验证Traceroute数据"""
    print("\n" + "="*60)
    print("Traceroute数据验证")
    print("="*60)
    
    total_traces = 0
    total_hops = 0
    gt_hops = 0
    hop_counts = []
    rtt_increases = []
    
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            
            total_traces += 1
            
            # 解析路径
            source_ip = parts[0]
            dest_ip = parts[1]
            
            hops = []
            rtts = []
            for i in range(2, len(parts), 2):
                if i + 1 < len(parts):
                    hops.append(parts[i])
                    rtts.append(float(parts[i + 1]))
            
            hop_counts.append(len(hops))
            total_hops += len(hops)
            
            # 统计GT IP
            for hop in hops:
                if hop in gt_ips:
                    gt_hops += 1
            
            # 统计RTT增长
            for i in range(1, len(rtts)):
                rtt_increases.append(rtts[i] - rtts[i-1])
    
    print(f"\n基本统计:")
    print(f"  总路径数: {total_traces}")
    print(f"  总跳数: {total_hops}")
    print(f"  平均跳数: {total_hops / total_traces:.1f}")
    print(f"  跳数范围: {min(hop_counts)} - {max(hop_counts)}")
    
    print(f"\nGround Truth覆盖:")
    print(f"  包含GT IP的跳数: {gt_hops}")
    print(f"  GT IP覆盖率: {gt_hops / total_hops * 100:.1f}%")
    
    print(f"\nRTT统计:")
    print(f"  平均RTT增长: {sum(rtt_increases) / len(rtt_increases):.2f} ms/跳")
    print(f"  RTT增长范围: {min(rtt_increases):.2f} - {max(rtt_increases):.2f} ms")


def main():
    """主函数"""
    print("="*60)
    print("数据验证工具")
    print("="*60)
    
    gt_file = Path("data/ground_truth/ground_truth.csv")
    tr_file = Path("data/traceroute/traceroute_sample.txt")
    
    if not gt_file.exists():
        print(f"\n错误: Ground Truth文件不存在: {gt_file}")
        print("请先运行: python scripts/generate_sample_data.py")
        return
    
    if not tr_file.exists():
        print(f"\n错误: Traceroute文件不存在: {tr_file}")
        print("请先运行: python scripts/generate_sample_data.py")
        return
    
    # 验证Ground Truth
    df = verify_ground_truth(str(gt_file))
    gt_ips = set(df['ip'].values)
    
    # 验证Traceroute
    verify_traceroute(str(tr_file), gt_ips)
    
    print("\n" + "="*60)
    print("✓ 数据验证完成")
    print("="*60)


if __name__ == '__main__':
    main()
