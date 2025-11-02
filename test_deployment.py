#!/usr/bin/env python3
"""
部署测试脚本
用于验证应用在生产环境中的基本功能
"""

import sys
import os

def test_imports():
    """测试所有必要的导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试Flask应用导入
        from app import app
        print("✅ Flask应用导入成功")
        
        # 测试配置导入
        from config import Config
        print("✅ 配置导入成功")
        
        # 测试工具模块导入
        from utils.encryption_engine import EncryptionEngine
        from utils.file_processor import FileProcessor
        from utils.password_book import PasswordBookManager
        print("✅ 所有工具模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置设置"""
    print("\n🔍 测试配置设置...")
    
    try:
        from config import Config
        
        # 检查必要的配置项
        required_configs = [
            'SECRET_KEY',
            'MAX_CONTENT_LENGTH', 
            'UPLOAD_FOLDER',
            'ALLOWED_EXTENSIONS',
            'DENIED_EXTENSIONS'
        ]
        
        for config in required_configs:
            if hasattr(Config, config):
                print(f"✅ 配置项 {config} 存在")
            else:
                print(f"❌ 配置项 {config} 缺失")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_directories():
    """测试必要的目录结构"""
    print("\n🔍 测试目录结构...")
    
    required_dirs = [
        'static/uploads',
        'static/password_books',
        'templates',
        'utils'
    ]
    
    all_exists = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ 目录 {directory} 存在")
        else:
            print(f"❌ 目录 {directory} 缺失")
            all_exists = False
            
    return all_exists

def test_dependencies():
    """测试依赖安装"""
    print("\n🔍 测试依赖安装...")
    
    required_packages = [
        'flask',
        'werkzeug', 
        'cryptography'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ 依赖 {package} 已安装")
        except ImportError:
            print(f"❌ 依赖 {package} 未安装")
            all_installed = False
            
    return all_installed

def main():
    """主测试函数"""
    print("🚀 开始部署测试...\n")
    
    tests = [
        test_imports,
        test_config, 
        test_directories,
        test_dependencies
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"测试 {i+1}: {status}")
    
    print(f"\n总测试: {total}, 通过: {passed}, 失败: {total - passed}")
    
    if all(results):
        print("\n🎉 所有测试通过！应用已准备好部署。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())