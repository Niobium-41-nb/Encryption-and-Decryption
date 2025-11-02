# 🚀 文件加密应用部署指南

## 推荐部署方式

### 1. Railway (最简单)
**步骤：**
1. 访问 [Railway](https://railway.app)
2. 使用 GitHub 登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择您的仓库
5. Railway 会自动检测并部署
6. 在设置中添加环境变量：`SECRET_KEY=your-secret-key`

**优点：**
- 完全自动化
- 免费额度充足
- 无需配置

### 2. Render (推荐)
**步骤：**
1. 访问 [Render](https://render.com)
2. 连接 GitHub 账户
3. 点击 "New" → "Web Service"
4. 选择您的仓库
5. 使用以下配置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
6. 添加环境变量：`SECRET_KEY`

### 3. PythonAnywhere (传统方式)
**步骤：**
1. 注册 [PythonAnywhere](https://pythonanywhere.com)
2. 上传项目文件
3. 创建虚拟环境：
   ```bash
   mkvirtualenv --python=/usr/bin/python3.11 myenv
   pip install -r requirements.txt
   ```
4. 配置 WSGI 文件指向 `wsgi.py`

## GitHub Actions 配置

项目已配置以下 GitHub Actions 工作流：

### 1. `deploy-simple.yml` (推荐)
- ✅ 基础测试
- ✅ 依赖安装验证
- ✅ 构建部署包
- ✅ 生成部署状态

### 2. `ci-cd.yml`
- ✅ 完整测试套件
- ✅ 应用启动测试
- ✅ 模块导入验证
- ✅ 配置检查

## 环境变量配置

| 变量 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `SECRET_KEY` | ✅ | Flask应用密钥 | `your-production-secret` |
| `PORT` | ❌ | 服务端口 | 自动设置 |

## 部署验证

部署后访问应用，验证以下功能：
1. ✅ 首页加载正常
2. ✅ 文件上传功能
3. ✅ 加密/解密流程
4. ✅ 文件下载功能

## 故障排除

### 常见问题

**1. 导入错误**
```bash
# 检查依赖
pip install -r requirements.txt

# 检查Python路径
python -c "import sys; print(sys.path)"
```

**2. 文件权限错误**
```bash
# 确保静态目录可写
chmod -R 755 static/
```

**3. 环境变量未设置**
- 检查部署平台的环境变量配置
- 确保 `SECRET_KEY` 已设置

**4. 端口绑定失败**
- 确保使用 `$PORT` 环境变量
- 检查平台分配的端口

## 生产环境建议

1. **使用强密钥**: 生成随机 SECRET_KEY
2. **启用HTTPS**: 配置SSL证书
3. **设置文件大小限制**: 当前限制500MB
4. **定期备份**: 备份密码本文件
5. **监控日志**: 配置应用日志监控

## 技术支持

如果遇到部署问题：
1. 检查 GitHub Actions 日志
2. 查看平台部署日志
3. 验证环境变量设置
4. 测试本地运行是否正常

---

**🚀 现在就开始部署吧！推荐使用 Railway 获得最佳体验。**