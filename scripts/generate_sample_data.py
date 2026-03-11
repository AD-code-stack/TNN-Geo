"""
生成示例数据用于测试
"""
import random
import numpy as np
from pathlib import Path
from collections import defaultdict


def generate_sample_ground_truth(output_path: str, num_ips: int = 10000):
    """
    生成示例ground truth数据
    模拟真实的IP地理分布特征
    
    Args:
        output_path: 输出文件路径
        num_ips: IP数量
    """
    # 定义主要城市中心点（中国主要城市）
    cities = [
        {"name": "北京", "lat": 39.9042, "lon": 116.4074, "weight": 0.15},
        {"name": "上海", "lat": 31.2304, "lon": 121.4737, "weight": 0.15},
        {"name": "广州", "lat": 23.1291, "lon": 113.2644, "weight": 0.12},
        {"name": "深圳", "lat": 22.5431, "lon": 114.0579, "weight": 0.10},
        {"name": "成都", "lat": 30.5728, "lon": 104.0668, "weight": 0.08},
        {"name": "杭州", "lat": 30.2741, "lon": 120.1551, "weight": 0.07},
        {"name": "武汉", "lat": 30.5928, "lon": 114.3055, "weight": 0.06},
        {"name": "西安", "lat": 34.3416, "lon": 108.9398, "weight": 0.06},
        {"name": "南京", "lat": 32.0603, "lon": 118.7969, "weight": 0.05},
        {"name": "重庆", "lat": 29.5630, "lon": 106.5516, "weight": 0.05},
        {"name": "天津", "lat": 39.3434, "lon": 117.3616, "weight": 0.04},
        {"name": "苏州", "lat": 31.2989, "lon": 120.5853, "weight": 0.03},
        {"name": "郑州", "lat": 34.7466, "lon": 113.6253, "weight": 0.02},
        {"name": "长沙", "lat": 28.2282, "lon": 112.9388, "weight": 0.02},
    ]
    
    # 生成IP地址池（按/24网段组织，模拟真实IP分配）
    ip_ranges = []
    used_ips = set()
    
    with open(output_path, 'w') as f:
        f.write("ip,latitude,longitude\n")
        
        ips_generated = 0
        
        # 为每个城市生成IP
        for city in cities:
            city_ips = int(num_ips * city['weight'])
            
            # 每个城市有多个/24网段
            num_ranges = max(1, city_ips // 200)
            
            for _ in range(num_ranges):
                # 生成一个/24网段
                base_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                
                # 在该网段内生成IP
                ips_in_range = min(200, city_ips - ips_generated)
                
                # 该网段的位置中心（在城市中心附近）
                range_lat = city['lat'] + np.random.normal(0, 0.1)
                range_lon = city['lon'] + np.random.normal(0, 0.1)
                
                for _ in range(ips_in_range):
                    # 生成该网段内的IP
                    host = random.randint(1, 254)
                    ip = f"{base_ip}.{host}"
                    
                    # 避免重复
                    if ip in used_ips:
                        continue
                    used_ips.add(ip)
                    
                    # 该IP的位置（在网段中心附近，模拟同一网段IP位置接近）
                    # 大部分IP在25km内（符合论文的m=25km参数）
                    distance_km = abs(np.random.normal(0, 8))  # 标准差8km
                    angle = random.uniform(0, 2 * np.pi)
                    
                    # 转换为经纬度偏移（粗略计算：1度约111km）
                    lat_offset = (distance_km * np.cos(angle)) / 111.0
                    lon_offset = (distance_km * np.sin(angle)) / (111.0 * np.cos(np.radians(range_lat)))
                    
                    lat = range_lat + lat_offset
                    lon = range_lon + lon_offset
                    
                    f.write(f"{ip},{lat:.6f},{lon:.6f}\n")
                    ips_generated += 1
                    
                    if ips_generated >= num_ips:
                        break
                
                if ips_generated >= num_ips:
                    break
            
            if ips_generated >= num_ips:
                break
    
    print(f"✓ 生成了 {ips_generated} 个ground truth IP")
    print(f"  - 覆盖 {len(cities)} 个城市")
    print(f"  - 模拟真实IP地理分布特征")
    print(f"  - 保存到: {output_path}")


def generate_sample_traceroute(output_path: str, ground_truth_path: str, num_traces: int = 5000):
    """
    生成示例traceroute数据
    基于ground truth生成更真实的traceroute路径
    
    Args:
        output_path: 输出文件路径
        ground_truth_path: ground truth文件路径
        num_traces: traceroute数量
    """
    # 读取ground truth IP
    gt_ips = []
    with open(ground_truth_path, 'r') as f:
        next(f)  # 跳过表头
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                gt_ips.append(parts[0])
    
    print(f"  从ground truth加载了 {len(gt_ips)} 个IP")
    
    # 定义骨干网节点（模拟互联网骨干路由器）
    backbone_nodes = []
    for i in range(50):
        backbone_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}." \
                     f"{random.randint(0, 255)}.{random.randint(1, 254)}"
        backbone_nodes.append(backbone_ip)
    
    with open(output_path, 'w') as f:
        f.write("# source_ip dest_ip hop1 rtt1 hop2 rtt2 ...\n")
        
        for i in range(num_traces):
            # 随机选择源IP和目标IP（优先从ground truth中选择）
            if random.random() < 0.7 and len(gt_ips) > 0:
                source_ip = random.choice(gt_ips)
            else:
                source_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}." \
                           f"{random.randint(0, 255)}.{random.randint(1, 254)}"
            
            if random.random() < 0.7 and len(gt_ips) > 0:
                dest_ip = random.choice(gt_ips)
            else:
                dest_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}." \
                         f"{random.randint(0, 255)}.{random.randint(1, 254)}"
            
            # 确保源和目标不同
            if source_ip == dest_ip:
                continue
            
            # 生成路径（8-20跳，模拟真实互联网路径）
            num_hops = random.randint(8, 20)
            
            line = f"{source_ip} {dest_ip}"
            
            # 初始RTT（本地网络）
            current_rtt = random.uniform(0.5, 2.0)
            
            hops = []
            
            for j in range(num_hops):
                # 决定这一跳的类型
                hop_type = random.random()
                
                if hop_type < 0.3 and len(gt_ips) > 0:
                    # 30%概率：使用ground truth IP（模拟经过已知位置的路由器）
                    hop_ip = random.choice(gt_ips)
                elif hop_type < 0.5:
                    # 20%概率：使用骨干网节点
                    hop_ip = random.choice(backbone_nodes)
                else:
                    # 50%概率：生成随机IP
                    hop_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}." \
                            f"{random.randint(0, 255)}.{random.randint(1, 254)}"
                
                # 避免重复跳
                if hop_ip in hops:
                    continue
                hops.append(hop_ip)
                
                # RTT增长模式
                if j < 3:
                    # 前几跳：本地网络，RTT增长较慢
                    rtt_increase = random.uniform(0.2, 1.0)
                elif j < num_hops - 3:
                    # 中间跳：骨干网，RTT增长中等
                    rtt_increase = random.uniform(1.0, 5.0)
                else:
                    # 最后几跳：目标网络，RTT增长较慢
                    rtt_increase = random.uniform(0.2, 1.5)
                
                current_rtt += rtt_increase
                
                # 添加一些随机抖动（模拟网络延迟波动）
                jitter = random.uniform(-0.5, 0.5)
                current_rtt = max(0.1, current_rtt + jitter)
                
                line += f" {hop_ip} {current_rtt:.2f}"
            
            f.write(line + "\n")
            
            # 进度提示
            if (i + 1) % 1000 == 0:
                print(f"  已生成 {i + 1}/{num_traces} 条traceroute...")
    
    print(f"✓ 生成了 {num_traces} 条traceroute记录")
    print(f"  - 平均路径长度: 8-20跳")
    print(f"  - 包含ground truth IP作为路由节点")
    print(f"  - 模拟真实网络延迟特征")
    print(f"  - 保存到: {output_path}")


def generate_statistics(gt_path: str, tr_path: str):
    """
    生成数据统计信息
    
    Args:
        gt_path: ground truth文件路径
        tr_path: traceroute文件路径
    """
    print("\n" + "="*60)
    print("数据统计")
    print("="*60)
    
    # Ground Truth统计
    gt_ips = set()
    cities = defaultdict(int)
    
    with open(gt_path, 'r') as f:
        next(f)  # 跳过表头
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                gt_ips.add(parts[0])
    
    print(f"\nGround Truth:")
    print(f"  - 总IP数: {len(gt_ips)}")
    
    # 统计/24网段数量
    ranges = set()
    for ip in gt_ips:
        parts = ip.split('.')
        if len(parts) == 4:
            range_id = f"{parts[0]}.{parts[1]}.{parts[2]}"
            ranges.add(range_id)
    
    print(f"  - /24网段数: {len(ranges)}")
    print(f"  - 平均每网段IP数: {len(gt_ips) / len(ranges):.1f}")
    
    # Traceroute统计
    total_traces = 0
    total_hops = 0
    gt_hops = 0
    
    with open(tr_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            
            total_traces += 1
            
            # 计算跳数
            num_hops = (len(parts) - 2) // 2
            total_hops += num_hops
            
            # 统计包含ground truth IP的跳数
            for i in range(2, len(parts), 2):
                if parts[i] in gt_ips:
                    gt_hops += 1
    
    print(f"\nTraceroute:")
    print(f"  - 总路径数: {total_traces}")
    print(f"  - 平均跳数: {total_hops / total_traces:.1f}")
    print(f"  - 包含GT IP的跳数: {gt_hops}")
    print(f"  - GT IP覆盖率: {gt_hops / total_hops * 100:.1f}%")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    print("="*60)
    print("IP地理定位 - 样本数据生成器")
    print("="*60)
    print()
    
    # 创建数据目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    gt_dir = data_dir / "ground_truth"
    gt_dir.mkdir(exist_ok=True)
    
    tr_dir = data_dir / "traceroute"
    tr_dir.mkdir(exist_ok=True)
    
    output_dir = data_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    gt_file = gt_dir / "ground_truth.csv"
    tr_file = tr_dir / "traceroute_sample.txt"
    
    # 生成示例数据
    print("[1/3] 生成Ground Truth数据...")
    print("-" * 60)
    generate_sample_ground_truth(
        str(gt_file),
        num_ips=10000
    )
    
    print("\n[2/3] 生成Traceroute数据...")
    print("-" * 60)
    generate_sample_traceroute(
        str(tr_file),
        str(gt_file),
        num_traces=5000
    )
    
    print("\n[3/3] 生成统计信息...")
    print("-" * 60)
    generate_statistics(str(gt_file), str(tr_file))
    
    print("\n" + "="*60)
    print("✓ 样本数据生成完成！")
    print("="*60)
    print("\n数据位置:")
    print(f"  Ground Truth: {gt_file}")
    print(f"  Traceroute:   {tr_file}")
    print(f"  输出目录:     {output_dir}")
    print("\n下一步:")
    print("  运行主程序: python main.py")
    print("="*60)


if __name__ == '__main__':
    main()
