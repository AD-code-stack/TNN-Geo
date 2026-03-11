"""
可视化结果
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from ..src.utils.geo_utils import haversine_distance


def plot_ip_distribution(ground_truth_file: str, output_file: str = None):
    """
    绘制IP地理分布图
    
    Args:
        ground_truth_file: ground truth文件路径
        output_file: 输出文件路径
    """
    df = pd.read_csv(ground_truth_file)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    scatter = ax.scatter(df['longitude'], df['latitude'], 
                        alpha=0.5, s=10, c='blue')
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('IP Geographic Distribution')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"保存到: {output_file}")
    else:
        plt.show()


def plot_range_coverage(ranges_file: str, output_file: str = None):
    """
    绘制IP范围覆盖图
    
    Args:
        ranges_file: IP范围文件路径
        output_file: 输出文件路径
    """
    df = pd.read_csv(ranges_file)
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # IP数量分布
    axes[0].hist(df['ip_count'], bins=30, edgecolor='black')
    axes[0].set_xlabel('Number of IPs per Range')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('IP Count Distribution per Range')
    axes[0].grid(True, alpha=0.3)
    
    # 最大距离分布
    axes[1].hist(df['max_distance'], bins=30, edgecolor='black')
    axes[1].set_xlabel('Max Distance (km)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Max Distance Distribution per Range')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"保存到: {output_file}")
    else:
        plt.show()


def plot_neighbor_validation(neighbors_file: str, output_file: str = None):
    """
    绘制延迟邻居验证图
    
    Args:
        neighbors_file: 邻居文件路径
        output_file: 输出文件路径
    """
    df = pd.read_csv(neighbors_file)
    
    if 'actual_distance' not in df.columns:
        print("警告: 邻居文件中没有actual_distance列，无法绘制验证图")
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # 延迟差 vs 实际距离
    axes[0].scatter(df['latency_diff'], df['actual_distance'], 
                   alpha=0.5, s=10)
    axes[0].set_xlabel('Latency Difference (ms)')
    axes[0].set_ylabel('Actual Distance (km)')
    axes[0].set_title('Latency Difference vs Actual Distance')
    axes[0].grid(True, alpha=0.3)
    
    # 距离分布
    axes[1].hist(df['actual_distance'], bins=50, edgecolor='black')
    axes[1].set_xlabel('Actual Distance (km)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Distance Distribution of Neighbor Pairs')
    axes[1].axvline(x=10, color='r', linestyle='--', label='10km threshold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"保存到: {output_file}")
    else:
        plt.show()


def main():
    """主函数"""
    output_dir = Path("data/output")
    
    if not output_dir.exists():
        print("错误: 输出目录不存在，请先运行主程序")
        return
    
    print("生成可视化图表...")
    print("-" * 60)
    
    # IP分布图
    gt_file = Path("data/ground_truth/ground_truth.csv")
    if gt_file.exists():
        print("绘制IP地理分布图...")
        plot_ip_distribution(
            str(gt_file),
            str(output_dir / "ip_distribution.png")
        )
    
    # IP范围覆盖图
    ranges_file = output_dir / "ip_ranges.csv"
    if ranges_file.exists():
        print("绘制IP范围覆盖图...")
        plot_range_coverage(
            str(ranges_file),
            str(output_dir / "range_coverage.png")
        )
    
    # 邻居验证图
    neighbors_file = output_dir / "latency_neighbors_high_accuracy.csv"
    if neighbors_file.exists():
        print("绘制延迟邻居验证图...")
        plot_neighbor_validation(
            str(neighbors_file),
            str(output_dir / "neighbor_validation.png")
        )
    
    print("-" * 60)
    print("可视化完成！")


if __name__ == '__main__':
    main()
