"""
IP地理定位主程序
实现论文方法：Traceroute位置传播与IP范围插值
"""
from pathlib import Path

from src.utils.config_loader import ConfigLoader
from src.data_processing.traceroute_parser import TracerouteParser
from src.data_processing.ground_truth_loader import GroundTruthLoader
from src.latency_neighbors.neighbor_extractor import LatencyNeighborExtractor
from src.ip_range_interpolation.range_interpolator import IPRangeInterpolator
from src.location_propagation.propagator import LocationPropagator


def main():
    """主函数"""
    print("="*60)
    print("IP地理定位 - Traceroute位置传播与IP范围插值")
    print("="*60)
    
    # 1. 加载配置
    print("\n[1/5] 加载配置...")
    config = ConfigLoader()
    data_paths = config.get_data_paths()
    
    # 创建输出目录
    output_dir = Path(data_paths['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 加载Ground Truth数据
    print("\n[2/5] 加载Ground Truth数据...")
    gt_loader = GroundTruthLoader(data_paths['ground_truth_file'])
    ground_truth = gt_loader.ip_to_location
    print(f"  加载了 {len(ground_truth)} 个IP的位置信息")
    
    # 3. 解析Traceroute数据
    print("\n[3/5] 解析Traceroute数据...")
    parser = TracerouteParser()
    traceroutes = parser.parse_directory(data_paths['traceroute_dir'])
    print(f"  解析了 {len(traceroutes)} 条traceroute记录")
    
    # 4. 提取延迟邻居
    print("\n[4/5] 提取延迟邻居...")
    
    # 高准确性配置
    print("  配置: 高准确性")
    ln_config_high = config.get_latency_neighbors_config('high_accuracy')
    extractor_high = LatencyNeighborExtractor(
        max_latency_diff=ln_config_high['max_latency_diff'],
        max_rtt=ln_config_high['max_rtt'],
        use_median=config.get('latency_neighbors.use_median_rtt'),
        min_instances=config.get('latency_neighbors.min_traceroute_instances')
    )
    neighbors_high = extractor_high.extract_neighbors(traceroutes, ground_truth)
    print(f"    提取了 {len(neighbors_high)} 个延迟邻居对")
    extractor_high.save(output_dir / 'latency_neighbors_high_accuracy.csv')
    
    # 高覆盖率配置
    print("  配置: 高覆盖率")
    ln_config_cov = config.get_latency_neighbors_config('high_coverage')
    extractor_cov = LatencyNeighborExtractor(
        max_latency_diff=ln_config_cov['max_latency_diff'],
        max_rtt=ln_config_cov['max_rtt'],
        use_median=config.get('latency_neighbors.use_median_rtt'),
        min_instances=config.get('latency_neighbors.min_traceroute_instances')
    )
    neighbors_cov = extractor_cov.extract_neighbors(traceroutes, ground_truth)
    print(f"    提取了 {len(neighbors_cov)} 个延迟邻居对")
    extractor_cov.save(output_dir / 'latency_neighbors_high_coverage.csv')
    
    # 5. IP范围插值
    print("\n[5/5] IP范围插值...")
    ip_config = config.get_ip_range_config()
    interpolator = IPRangeInterpolator(
        range_size=ip_config['range_size'],
        min_ground_truth=ip_config['min_ground_truth'],
        max_distance_km=ip_config['max_distance_km'],
        netmask=ip_config['netmask']
    )
    
    # 执行插值
    interpolated = interpolator.interpolate(ground_truth)
    print(f"  插值后IP数量: {len(interpolated)}")
    
    # 计算覆盖率扩展
    expansion = interpolator.get_coverage_expansion(len(ground_truth), len(interpolated))
    print(f"  覆盖率扩展: {expansion['expansion_factor']:.1f}x")
    
    # 保存插值结果
    interpolator.save_ranges(output_dir / 'ip_ranges.csv')
    interpolator.save_interpolated(interpolated, output_dir / 'interpolated_ips.csv')
    
    # 6. 位置传播
    print("\n[6/5] 位置传播...")
    prop_config = config.get_propagation_config()
    propagator = LocationPropagator(
        max_iterations=prop_config['max_iterations'],
        convergence_threshold=prop_config['convergence_threshold']
    )
    
    # 初始化已知位置
    propagator.initialize(interpolated)
    
    # 选择邻居配置
    mode = prop_config['mode']
    if mode == 'high_accuracy':
        neighbors = neighbors_high
        print("  使用高准确性配置")
    else:
        neighbors = neighbors_cov
        print("  使用高覆盖率配置")
    
    # 执行传播
    propagated = propagator.propagate_via_neighbors(
        neighbors, 
        interpolator.ip_ranges
    )
    print(f"  传播了 {len(propagated)} 个新IP位置")
    
    # 保存传播结果
    propagator.save_propagated(output_dir / 'propagated_ips.csv')
    propagator.save_all_locations(output_dir / 'all_locations.csv')
    
    print("\n" + "="*60)
    print("完成！结果已保存到:", output_dir)
    print("="*60)


if __name__ == '__main__':
    main()
