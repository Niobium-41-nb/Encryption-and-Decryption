# 文件加密应用部署指南

## 项目概述
这是一个基于Flask的文件加密解密Web应用，支持多轮加密和密码本管理。

## 部署方式

### 1. GitHub Actions 自动部署

项目已配置GitHub Actions工作流，支持以下功能：

- **自动测试**: 在推送代码时运行基本导入测试
- **构建部署包**: 创建完整的部署包
- **多平台部署**: 支持Heroku、Railway等平台

### 2. 环境变量配置

部署时需要设置以下环境变量：

```bash
SECRET_KEY=your-secret-key-here  # Flask应用密钥
```

### 3. 支持的部署平台

#### Heroku 部署

**前提条件：**
- Heroku账户
- Heroku CLI工具

**部署步骤：**
1. 在Heroku创建新应用
2. 设置环境变量：
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   ```
3. 部署代码：
   ```bash
   git push heroku main
   ```

#### Railway 部署

1. 连接GitHub仓库到Railway
2. 设置环境变量
3. 自动部署

#### PythonAnywhere 部署

1. 上传项目文件
2. 创建虚拟环境并安装依赖
3. 配置WSGI文件指向`wsgi.py`
4. 设置环境变量

#### Vercel 部署（需要适配）

由于这是Flask应用，可能需要使用serverless适配器。

### 4. 本地开发运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export SECRET_KEY=your-secret-key

# 运行应用
python app.py
```

### 5. 生产环境运行

使用Gunicorn作为WSGI服务器：

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

### 6. 文件存储说明

- 上传文件存储在 `static/uploads/`
- 密码本文件存储在 `static/password_books/`
- 生产环境建议使用云存储服务（如AWS S3）

### 7. 安全注意事项

1. **密钥管理**: 生产环境务必使用强密钥
2. **文件大小限制**: 当前限制为500MB
3. **文件类型限制**: 已配置允许和禁止的文件类型
4. **临时文件清理**: 自动清理上传的临时文件

### 8. 监控和日志

- 应用内置了详细的日志记录
- 生产环境建议配置应用性能监控(APM)
- 错误页面已配置(404, 500, 413)

## 故障排除

### 常见问题

1. **导入错误**: 确保所有依赖已正确安装
2. **文件权限**: 确保应用有写入静态目录的权限
3. **内存不足**: 大文件处理可能需要更多内存

### 日志查看

应用使用Python标准logging模块，日志级别为DEBUG，可在生产环境中调整为INFO或WARNING。

## 扩展建议

1. **数据库集成**: 添加用户管理和文件元数据存储
2. **云存储**: 集成AWS S3或其他对象存储
3. **CDN**: 静态文件使用CDN加速
4. **缓存**: 添加Redis缓存支持