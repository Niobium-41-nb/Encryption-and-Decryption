import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip',
        'tar', 'gz', 'bz2', 'doc', 'docx', 'xls', 'xlsx',
        'mp3', 'mp4', 'avi', 'mov'
    }
    DENIED_EXTENSIONS = {'exe', 'sh', 'bat', 'cmd', 'msi'}

    # 压缩算法支持
    COMPRESSION_ALGORITHMS = ['zip', 'tar', 'gzip', 'tar.gz', 'tar.bz2']
    
    # 后缀名池
    EXTENSION_POOL = [
        '.txt', '.jpg', '.pdf', '.docx', '.mp3', '.mp4',
        '.png', '.xlsx', '.zip', '.tar', '.gz'
    ]

    # 临时文件清理时间（秒）
    TEMP_FILE_CLEANUP_TIME = 3600  # 1小时