"""
评估器
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
from ..utils.geo_utils import haversine_distance


class Evaluator:
    """IP地理定位评估器"""
    
    def __init__(self):
        """初始化评估器"""
        self.results = {}
    
    def evaluate(self, predictions: Dict[str, Tuple[float, float]],
                ground_truth: Dict[str, Tuple[float, float]],
                name: str = "default") -> Dict:
        """
        评估预测结果
        
        Args:
            predictions: 预测的IP位置
            ground_truth: 真实的IP位置
            name: 评估名称
        
        Returns:
            评估指标字典
        """
        errors = []
        
        for ip, pred_loc in predictions.items():
            if ip in ground_truth:
                true_loc = ground_truth[ip]
                error = haversine_distance(
                    true_loc[0], true_loc[1],
                    pred_loc[0], pred_loc[1]
                )
                errors.append(error)
        
        if not errors:
            return {'error': 'No common IPs between predictions and ground truth'}
        
        # 计算基本统计指标
        median_error = np.median(errors)
        mae = np.mean(errors)
        rmse = np.sqrt(np.mean([e**2 for e in errors]))
        
        # 计算不同距离阈值内的覆盖率
        thresholds = [5, 10, 20, 50, 100]
        coverage = {}
        for threshold in thresholds:
            within = sum(1 for e in errors if e <= threshold)
            coverage[f'coverage_{threshold}km'] = within / len(errors)
        
        # 计算百分位数
        percentiles = [25, 50, 75, 90, 95, 99]
        percentile_errors = {}
        for p in percentiles:
            percentile_errors[f'p{p}'] = np.percentile(errors, p)
        
        results = {
            'name': name,
            'total_predictions': len(predictions),
            'evaluated': len(errors),
            'median_error_km': median_error,
            'mae_km': mae,
            'rmse_km': rmse,
            'min_error_km': np.min(errors),
            'max_error_km': np.max(errors),
            'std_error_km': np.std(errors),
            **coverage,
            **percentile_errors
        }
        
        self.results[name] = {
            'metrics': results,
            'errors': errors
        }
        
        return results
    
    def compare_methods(self, methods: Dict[str, Dict[str, Tuple[float, float]]],
                       ground_truth: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
        """
        比较多个方法
        
        Args:
            methods: {method_name: predictions} 字典
            ground_truth: 真实位置
        
        Returns:
            比较结果DataFrame
        """
        comparison = []
        
        for method_name, predictions in methods.items():
            metrics = self.evaluate(predictions, ground_truth, method_name)
            comparison.append(metrics)
        
        return pd.DataFrame(comparison)
    
    def plot_error_distribution(self, name: str = None, save_path: str = None):
        """
        绘制误差分布图
        
        Args:
            name: 评估名称（None表示所有）
            save_path: 保存路径
        """
        if name:
            names = [name]
        else:
            names = list(self.results.keys())
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        for name in names:
            if name not in self.results:
                continue
            
            errors = self.results[name]['errors']
            
            # 直方图
            axes[0].hist(errors, bins=50, alpha=0.7, label=name)
            axes[0].set_xlabel('Error (km)')
            axes[0].set_ylabel('Frequency')
            axes[0].set_title('Error Distribution')
            axes[0].legend()
            
            # CDF
            sorted_errors = np.sort(errors)
            cdf = np.arange(1, len(sorted_errors) + 1) / len(sorted_errors)
            axes[1].plot(sorted_errors, cdf, label=name)
            axes[1].set_xlabel('Error (km)')
            axes[1].set_ylabel('CDF')
            axes[1].set_title('Cumulative Distribution Function')
            axes[1].legend()
            axes[1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def plot_comparison(self, save_path: str = None):
        """
        绘制方法比较图
        
        Args:
            save_path: 保存路径
        """
        if not self.results:
            print("No results to plot")
            return
        
        # 准备数据
        names = list(self.results.keys())
        metrics = ['median_error_km', 'mae_km', 'rmse_km']
        
        data = []
        for name in names:
            for metric in metrics:
                value = self.results[name]['metrics'][metric]
                data.append({
                    'Method': name,
                    'Metric': metric,
                    'Value': value
                })
        
        df = pd.DataFrame(data)
        
        # 绘图
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.barplot(data=df, x='Method', y='Value', hue='Metric', ax=ax)
        ax.set_ylabel('Error (km)')
        ax.set_title('Method Comparison')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def plot_coverage_comparison(self, save_path: str = None):
        """
        绘制覆盖率比较图
        
        Args:
            save_path: 保存路径
        """
        if not self.results:
            print("No results to plot")
            return
        
        # 准备数据
        thresholds = [5, 10, 20, 50, 100]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for name, result in self.results.items():
            metrics = result['metrics']
            coverages = [metrics[f'coverage_{t}km'] * 100 for t in thresholds]
            ax.plot(thresholds, coverages, marker='o', label=name)
        
        ax.set_xlabel('Distance Threshold (km)')
        ax.set_ylabel('Coverage (%)')
        ax.set_title('Coverage vs Distance Threshold')
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
    
    def save_results(self, output_path: str):
        """
        保存评估结果
        
        Args:
            output_path: 输出文件路径
        """
        data = []
        
        for name, result in self.results.items():
            data.append(result['metrics'])
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    
    def print_summary(self, name: str = None):
        """
        打印评估摘要
        
        Args:
            name: 评估名称（None表示所有）
        """
        if name:
            names = [name]
        else:
            names = list(self.results.keys())
        
        for name in names:
            if name not in self.results:
                continue
            
            metrics = self.results[name]['metrics']
            
            print(f"\n{'='*60}")
            print(f"Evaluation Results: {name}")
            print(f"{'='*60}")
            print(f"Total Predictions: {metrics['total_predictions']}")
            print(f"Evaluated: {metrics['evaluated']}")
            print(f"\nError Metrics:")
            print(f"  Median Error: {metrics['median_error_km']:.2f} km")
            print(f"  MAE: {metrics['mae_km']:.2f} km")
            print(f"  RMSE: {metrics['rmse_km']:.2f} km")
            print(f"\nCoverage:")
            for threshold in [5, 10, 20, 50, 100]:
                coverage = metrics[f'coverage_{threshold}km'] * 100
                print(f"  <{threshold}km: {coverage:.1f}%")
