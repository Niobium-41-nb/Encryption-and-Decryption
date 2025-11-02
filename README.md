# 基于Flask的文件加密解密系统

一个基于Flask框架实现的文件加密解密系统，通过多轮压缩和修改后缀名的方式实现文件加密，并生成密码本记录加密过程。

## 功能特性

### 🔒 核心功能
- **多轮加密**: 支持1-10轮加密，每轮包含压缩和修改后缀名两个步骤
- **随机算法**: 随机选择压缩算法（zip、tar、gzip、tar.gz、tar.bz2）和后缀名
- **密码本管理**: 自动生成JSON格式密码本，记录完整的加密过程
- **批量操作**: 支持多文件同时加密解密
- **安全存储**: 支持密码本加密保护

### 🛡️ 安全特性
- 临时文件自动清理机制
- 文件类型白名单验证
- 最大文件大小限制（500MB）
- 会话隔离保护
- 密码本AES加密选项

### 🎯 用户体验
- 响应式Web界面（Bootstrap 5）
- 文件拖放上传支持
- 实时进度显示
- 操作结果预览
- 错误友好提示

## 系统架构

```
file-encryption-system/
├── app.py                 # Flask主应用
├── config.py             # 应用配置
├── requirements.txt      # Python依赖
├── utils/                # 核心工具模块
│   ├── file_processor.py # 文件处理
│   ├── encryption_engine.py # 加密引擎
│   └── password_book.py  # 密码本管理
├── templates/            # HTML模板
├── static/               # 静态资源
│   ├── css/style.css
│   ├── js/main.js
│   ├── uploads/          # 临时上传目录
│   └── password_books/   # 密码本存储
└── README.md
```

## 安装部署

### 环境要求
- Python 3.7+
- Windows/Linux/macOS

### 快速开始

1. **克隆或下载项目**
```bash
git clone <repository-url>
cd file-encryption-system
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python app.py
```

4. **访问系统**
打开浏览器访问: http://localhost:5000

### 生产部署

对于生产环境，建议使用：
- Gunicorn + Nginx
- 配置适当的文件存储
- 设置环境变量

## 使用指南

### 文件加密流程

1. **上传文件**
   - 支持单文件或批量上传
   - 最大文件大小500MB
   - 支持常见文件类型

2. **配置加密参数**
   - 设置加密轮数（1-10轮）
   - 可选择手动设置或特定代码生成
   - 可选密码本加密

3. **执行加密**
   - 系统自动执行多轮加密
   - 每轮：压缩 → 修改后缀名
   - 生成加密文件和密码本

4. **下载结果**
   - 下载加密后的文件
   - 下载对应的密码本
   - 妥善保存密码本

### 文件解密流程

1. **上传加密文件和密码本**
   - 上传需要解密的文件
   - 上传对应的密码本（JSON格式）
   - 如密码本已加密，输入解密密码

2. **执行解密**
   - 系统验证密码本格式
   - 反向执行加密步骤
   - 验证文件完整性

3. **下载解密文件**
   - 下载还原的原始文件
   - 验证文件内容

### 密码本管理

- **查看列表**: 查看所有生成的密码本
- **下载**: 下载密码本文件
- **删除**: 删除不需要的密码本
- **详情**: 查看密码本结构和内容

## 技术实现

### 加密算法

```python
# 加密流程示例
def multi_round_encrypt(file_path, rounds):
    current_file = file_path
    password_book = {}
    
    for round_num in range(1, rounds + 1):
        # 1. 压缩
        algorithm = random.choice(COMPRESSION_ALGORITHMS)
        compressed_file = compress_file(current_file, algorithm)
        
        # 2. 修改后缀名
        new_extension = random.choice(EXTENSION_POOL)
        encrypted_file = change_extension(compressed_file, new_extension)
        
        # 记录到密码本
        password_book[round_num] = {
            'extension': new_extension,
            'algorithm': algorithm
        }
        
        current_file = encrypted_file
    
    return current_file, password_book
```

### 密码本格式

```json
{
  "metadata": {
    "encryption_time": "2025-11-02T14:30:00",
    "total_rounds": 3,
    "original_filename": "example.pdf",
    "original_hash": "d41d8cd98f00b204e9800998ecf8427e"
  },
  "rounds": {
    "1": {
      "extension": ".jpg",
      "algorithm": "zip"
    },
    "2": {
      "extension": ".txt",
      "algorithm": "tar.gz"
    },
    "3": {
      "extension": ".mp3", 
      "algorithm": "gzip"
    }
  }
}
```

## 配置说明

### 主要配置项

```python
# config.py
class Config:
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB文件大小限制
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', ...}  # 允许的文件类型
    DENIED_EXTENSIONS = {'exe', 'sh', 'bat', ...}  # 禁止的文件类型
    COMPRESSION_ALGORITHMS = ['zip', 'tar', 'gzip', 'tar.gz', 'tar.bz2']  # 压缩算法
    EXTENSION_POOL = ['.txt', '.jpg', '.pdf', ...]  # 后缀名池
```

### 环境变量

- `SECRET_KEY`: Flask应用密钥
- 其他配置可通过环境变量覆盖

## 安全注意事项

1. **文件安全**
   - 系统不长期存储用户文件
   - 临时文件1小时后自动清理
   - 文件访问会话隔离

2. **密码本安全**
   - 建议启用密码本加密功能
   - 妥善保管密码本文件
   - 避免密码本泄露

3. **使用建议**
   - 不要上传敏感个人信息
   - 定期清理不需要的密码本
   - 备份重要的加密文件和密码本

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查文件大小是否超过500MB
   - 验证文件类型是否支持
   - 检查网络连接

2. **加密/解密失败**
   - 验证密码本格式是否正确
   - 检查密码本是否匹配加密文件
   - 确认密码本解密密码（如设置）

3. **系统性能问题**
   - 大文件处理需要较长时间
   - 建议分批处理大量文件
   - 确保服务器有足够磁盘空间

### 日志查看

系统运行日志会显示在控制台，包含：
- 文件上传状态
- 加密解密过程
- 错误信息详情

## 扩展开发

### 添加新的压缩算法

1. 在 `config.py` 的 `COMPRESSION_ALGORITHMS` 中添加算法名称
2. 在 `utils/file_processor.py` 中实现对应的压缩/解压方法

### 自定义后缀名池

修改 `config.py` 中的 `EXTENSION_POOL` 列表，添加或删除后缀名。

### API扩展

系统基于Flask框架，可以轻松扩展REST API接口供其他应用调用。

## 许可证

本项目采用MIT许可证。

## 技术支持

如有问题或建议，请提交Issue或联系开发团队。

---

**版本**: 1.0  
**最后更新**: 2025-11-02