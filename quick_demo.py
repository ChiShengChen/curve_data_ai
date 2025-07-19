#!/usr/bin/env python3
"""
Curve智能重新平衡系统快速演示
运行此脚本来快速测试系统功能
"""

import os
import sys

def run_demo():
    print("🚀 Curve智能重新平衡系统 - 快速演示")
    print("=" * 50)
    
    # 检查是否有训练好的模型
    if not os.path.exists('best_curve_model.pth'):
        print("📚 第一次运行，需要训练模型...")
        print("正在训练模型，这可能需要几分钟时间...")
        
        # 运行训练脚本（较少的epochs用于演示）
        import subprocess
        result = subprocess.run([
            sys.executable, 'train_curve_model.py',
            '--epochs', '20',
            '--num_samples', '5000',
            '--batch_size', '64'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ 训练失败:")
            print(result.stderr)
            return False
        
        print("✅ 模型训练完成!")
    else:
        print("✅ 找到已训练的模型")
    
    print("\n🔍 运行单次预测演示...")
    
    # 运行预测演示
    import subprocess
    result = subprocess.run([
        sys.executable, 'run_curve_rebalancer.py',
        '--mode', 'single',
        '--dry_run'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("预测结果:")
        print(result.stdout)
    else:
        print("❌ 预测失败:")
        print(result.stderr)
        return False
    
    print("\n" + "=" * 50)
    print("🎉 演示完成! 你可以:")
    print("1. 查看训练曲线: training_curve.png")
    print("2. 使用监控模式: python run_curve_rebalancer.py --mode monitor")
    print("3. 查看详细说明: README.md")
    
    return True

if __name__ == "__main__":
    success = run_demo()
    if not success:
        sys.exit(1) 