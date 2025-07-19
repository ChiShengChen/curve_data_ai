#!/usr/bin/env python3
"""
Curve智能重新平衡主运行脚本
"""

import torch
import argparse
import time
from datetime import datetime
import json

from curve_rebalancer import CurvePoolPredictor, CurveDataCollector, CurveRebalancer

def load_trained_model(model_path: str = 'best_curve_model.pth', input_dim: int = 5) -> tuple:
    """加载训练好的模型"""
    
    print(f"Loading model from {model_path}...")
    
    # 创建模型实例
    model = CurvePoolPredictor(input_dim=input_dim)
    
    try:
        # 加载检查点
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        scaler = checkpoint.get('scaler', None)
        
        print(f"Model loaded successfully!")
        print(f"  - Epoch: {checkpoint.get('epoch', 'N/A')}")
        print(f"  - Validation Loss: {checkpoint.get('val_loss', 'N/A'):.6f}")
        
        return model, scaler
        
    except FileNotFoundError:
        print(f"Error: Model file {model_path} not found!")
        print("Please train the model first using: python train_curve_model.py")
        return None, None
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

def run_single_prediction(args):
    """运行单次预测"""
    
    print("=== Curve智能重新平衡 - 单次预测模式 ===")
    
    # 加载模型
    model, scaler = load_trained_model(args.model_path)
    if model is None:
        return False
    
    # 初始化组件
    data_collector = CurveDataCollector(web3_provider=args.web3_provider)
    rebalancer = CurveRebalancer(model, data_collector)
    
    print(f"Target Pool: {args.pool_address}")
    print(f"Lookback Hours: {args.lookback_hours}")
    
    try:
        # 生成重新平衡信号
        signal = rebalancer.generate_rebalance_signal(
            args.pool_address, 
            args.lookback_hours
        )
        
        # 显示结果
        print("\n--- 预测结果 ---")
        print(f"Action: {signal.action}")
        print(f"Token: {signal.token}")
        print(f"Amount: ${signal.amount:,.2f}")
        print(f"Confidence: {signal.confidence:.3f}")
        print(f"Expected Profit: {signal.expected_profit:.6f}")
        print(f"Risk Score: {signal.risk_score:.3f}")
        
        # 如果启用执行模式，则执行重新平衡
        if args.execute and signal.action != 'hold':
            print("\n--- 执行重新平衡 ---")
            success = rebalancer.execute_rebalance(signal)
            
            if success:
                print("✅ 重新平衡执行成功!")
                
                # 保存交易记录
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'pool_address': args.pool_address,
                    'action': signal.action,
                    'token': signal.token,
                    'amount': signal.amount,
                    'confidence': signal.confidence,
                    'expected_profit': signal.expected_profit,
                    'risk_score': signal.risk_score
                }
                
                with open('trade_history.json', 'a') as f:
                    f.write(json.dumps(trade_record) + '\n')
                    
                print("📝 交易记录已保存到 trade_history.json")
            else:
                print("❌ 重新平衡执行失败!")
        elif args.execute:
            print("💤 无需执行操作 (Hold)")
        else:
            print("🔍 仅预测模式，未执行实际交易")
            
        return True
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        return False

def run_monitoring_mode(args):
    """运行监控模式"""
    
    print("=== Curve智能重新平衡 - 监控模式 ===")
    print(f"监控间隔: {args.interval} 分钟")
    print("按 Ctrl+C 停止监控")
    
    # 加载模型
    model, scaler = load_trained_model(args.model_path)
    if model is None:
        return False
    
    # 初始化组件
    data_collector = CurveDataCollector(web3_provider=args.web3_provider)
    rebalancer = CurveRebalancer(model, data_collector)
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检查池子状态...")
            
            try:
                # 生成重新平衡信号
                signal = rebalancer.generate_rebalance_signal(
                    args.pool_address, 
                    args.lookback_hours
                )
                
                print(f"Action: {signal.action}, Token: {signal.token}, "
                      f"Amount: ${signal.amount:,.2f}, Confidence: {signal.confidence:.3f}")
                
                # 如果有重要操作建议
                if signal.action != 'hold' and signal.confidence > 0.7:
                    print("🚨 检测到高置信度的重新平衡机会!")
                    
                    if args.execute:
                        success = rebalancer.execute_rebalance(signal)
                        if success:
                            print("✅ 自动执行重新平衡成功!")
                        else:
                            print("❌ 自动执行重新平衡失败!")
                    else:
                        print("💡 建议手动执行重新平衡操作")
                
            except Exception as e:
                print(f"监控循环中出错: {e}")
            
            # 等待下一次检查
            time.sleep(args.interval * 60)
            
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
        return True

def main():
    parser = argparse.ArgumentParser(description='Curve智能重新平衡系统')
    
    # 基本参数
    parser.add_argument('--pool_address', type=str, 
                       default='0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
                       help='Curve池地址 (默认: 3Pool)')
    parser.add_argument('--model_path', type=str, default='best_curve_model.pth',
                       help='训练好的模型路径')
    parser.add_argument('--web3_provider', type=str, 
                       help='Web3提供者URL (例如: https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY)')
    parser.add_argument('--lookback_hours', type=int, default=24,
                       help='回看时间（小时）')
    
    # 运行模式
    parser.add_argument('--mode', type=str, choices=['single', 'monitor'], 
                       default='single', help='运行模式: single (单次预测) 或 monitor (持续监控)')
    parser.add_argument('--interval', type=int, default=15,
                       help='监控模式下的检查间隔（分钟）')
    
    # 执行选项
    parser.add_argument('--execute', action='store_true',
                       help='启用实际执行模式（谨慎使用！）')
    parser.add_argument('--dry_run', action='store_true',
                       help='干运行模式，只显示预测结果')
    
    args = parser.parse_args()
    
    # 安全检查
    if args.execute and not args.dry_run:
        response = input("⚠️  您已启用实际执行模式，这将在区块链上执行真实交易！\n"
                        "确认继续? (输入 'YES' 确认): ")
        if response != 'YES':
            print("已取消执行模式")
            return
    
    # 显示配置
    print("=== 配置信息 ===")
    print(f"Pool Address: {args.pool_address}")
    print(f"Model Path: {args.model_path}")
    print(f"Web3 Provider: {args.web3_provider or 'None (使用模拟数据)'}")
    print(f"Mode: {args.mode}")
    print(f"Execute: {args.execute}")
    print()
    
    # 根据模式运行
    if args.mode == 'single':
        success = run_single_prediction(args)
    elif args.mode == 'monitor':
        success = run_monitoring_mode(args)
    else:
        print(f"未知模式: {args.mode}")
        success = False
    
    if success:
        print("✅ 程序执行完成")
    else:
        print("❌ 程序执行失败")

if __name__ == "__main__":
    main() 