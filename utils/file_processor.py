import os
import zipfile
import tarfile
import gzip
import shutil
import hashlib
import logging
from datetime import datetime
from config import Config

# 配置日志
logger = logging.getLogger(__name__)


class FileProcessor:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.denied_extensions = Config.DENIED_EXTENSIONS

        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)

    def validate_file(self, filename):
        """验证上传文件是否合法"""
        if not filename:
            return False, "文件名不能为空"

        # 获取文件扩展名
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        # 检查禁止的文件类型
        if file_ext in self.denied_extensions:
            return False, f"不支持的文件类型: .{file_ext}"

        # 检查允许的文件类型
        if file_ext not in self.allowed_extensions:
            return False, f"不支持的文件类型: .{file_ext}"

        return True, "文件验证通过"

    def save_uploaded_file(self, file):
        """保存上传文件到临时目录"""
        try:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
            filename = f"{timestamp}_{file_hash}_{file.filename}"
            filepath = os.path.join(self.upload_folder, filename)

            # 保存文件
            file.save(filepath)
            logger.debug(f"文件保存成功: {filepath}")
            return True, filepath, filename
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            return False, None, f"文件保存失败: {str(e)}"

    def compress_file(self, file_path, algorithm):
        """使用指定算法压缩文件"""
        try:
            base_name = os.path.splitext(file_path)[0]
            logger.debug(f"开始压缩文件: {file_path}, 算法: {algorithm}")

            if algorithm == 'zip':
                output_path = base_name + '.zip'
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_path, os.path.basename(file_path))

            elif algorithm == 'tar':
                output_path = base_name + '.tar'
                with tarfile.open(output_path, 'w') as tar:
                    tar.add(file_path, arcname=os.path.basename(file_path))

            elif algorithm == 'gzip':
                output_path = base_name + '.gz'
                with open(file_path, 'rb') as f_in:
                    with gzip.open(output_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

            elif algorithm == 'tar.gz':
                output_path = base_name + '.tar.gz'
                with tarfile.open(output_path, 'w:gz') as tar:
                    tar.add(file_path, arcname=os.path.basename(file_path))

            elif algorithm == 'tar.bz2':
                output_path = base_name + '.tar.bz2'
                with tarfile.open(output_path, 'w:bz2') as tar:
                    tar.add(file_path, arcname=os.path.basename(file_path))

            else:
                return False, None, f"不支持的压缩算法: {algorithm}"

            logger.debug(f"压缩成功: {file_path} -> {output_path}")
            return True, output_path, None

        except Exception as e:
            logger.error(f"压缩失败: {file_path} - {str(e)}")
            return False, None, f"压缩失败: {str(e)}"

    def extract_file(self, file_path, algorithm):
        """使用指定算法解压文件"""
        try:
            # 创建唯一的解压目录，避免路径冲突
            import time
            base_name = os.path.splitext(file_path)[0]
            timestamp = str(int(time.time() * 1000))
            extract_dir = f"{base_name}_extracted_{timestamp}"

            # 确保目录不存在，避免冲突
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

            os.makedirs(extract_dir, exist_ok=True)
            logger.debug(f"创建解压目录: {extract_dir}")

            output_path = None

            if algorithm == 'zip':
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    zipf.extractall(extract_dir)

                # 查找解压后的文件
                output_path = self._find_extracted_file(extract_dir, file_path)

            elif algorithm in ['tar', 'tar.gz', 'tar.bz2']:
                mode = 'r'
                if algorithm == 'tar.gz':
                    mode = 'r:gz'
                elif algorithm == 'tar.bz2':
                    mode = 'r:bz2'

                with tarfile.open(file_path, mode) as tar:
                    tar.extractall(extract_dir)

                # 查找解压后的文件
                output_path = self._find_extracted_file(extract_dir, file_path)

            elif algorithm == 'gzip':
                # 对于gzip，解压后是单个文件
                output_path = base_name  # 移除.gz扩展名
                with gzip.open(file_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                return False, None, f"不支持的解压算法: {algorithm}"

            if not output_path or not os.path.exists(output_path):
                logger.error(f"解压后未找到文件: {extract_dir}")
                # 返回解压目录作为备选
                output_path = extract_dir

            logger.debug(f"解压成功: {file_path} -> {output_path}")
            return True, output_path, None

        except Exception as e:
            logger.error(f"解压失败: {file_path} - {str(e)}")
            # 清理可能创建的部分目录
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                try:
                    shutil.rmtree(extract_dir)
                except Exception as cleanup_error:
                    logger.warning(f"清理解压目录失败: {cleanup_error}")
            return False, None, f"解压失败: {str(e)}"

    def _find_extracted_file(self, extract_dir, original_file_path):
        """在解压目录中查找解压后的文件"""
        try:
            # 获取原始文件名（不含路径和扩展名）
            original_filename = os.path.basename(original_file_path)
            original_name_without_ext = os.path.splitext(original_filename)[0]

            # 首先尝试查找与原始文件名匹配的文件
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_name_without_ext = os.path.splitext(file)[0]

                    # 如果文件名匹配（考虑多层加密的情况）
                    if (original_name_without_ext in file_name_without_ext or
                            file_name_without_ext in original_name_without_ext):
                        return file_path

            # 如果没有找到匹配的文件，返回第一个文件
            for root, dirs, files in os.walk(extract_dir):
                if files:
                    return os.path.join(root, files[0])

            # 如果没有任何文件，返回目录本身
            return extract_dir

        except Exception as e:
            logger.error(f"查找解压文件失败: {str(e)}")
            return extract_dir

    def change_extension(self, file_path, new_extension):
        """修改文件后缀名"""
        try:
            base_name = os.path.splitext(file_path)[0]
            new_file_path = base_name + new_extension

            # 如果目标文件已存在，先删除
            if os.path.exists(new_file_path):
                os.remove(new_file_path)

            os.rename(file_path, new_file_path)
            logger.debug(f"修改后缀名成功: {file_path} -> {new_file_path}")
            return True, new_file_path, None
        except Exception as e:
            logger.error(f"修改后缀名失败: {file_path} - {str(e)}")
            return False, None, f"修改后缀名失败: {str(e)}"

    def get_file_info(self, file_path):
        """获取文件信息"""
        try:
            stat = os.stat(file_path)
            return {
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'extension': os.path.splitext(file_path)[1]
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path} - {str(e)}")
            return None

    def cleanup_temp_files(self, file_paths=None):
        """清理临时文件"""
        try:
            if file_paths:
                # 清理指定文件和目录
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        if os.path.isdir(file_path):
                            # 检查是否是_extracted目录
                            if '_extracted' in file_path:
                                shutil.rmtree(file_path)
                                logger.debug(f"清理临时目录: {file_path}")
                            else:
                                # 对于非_extracted目录，更谨慎地处理
                                logger.debug(f"跳过清理非临时目录: {file_path}")
                        else:
                            # 只清理在uploads目录中的临时文件
                            if self.upload_folder in file_path:
                                os.remove(file_path)
                                logger.debug(f"清理临时文件: {file_path}")
                            else:
                                logger.debug(f"跳过清理非临时文件: {file_path}")
                return True, "清理完成"
            else:
                # 清理整个上传目录
                if os.path.exists(self.upload_folder):
                    for filename in os.listdir(self.upload_folder):
                        file_path = os.path.join(self.upload_folder, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path) and '_extracted' in filename:
                            shutil.rmtree(file_path)
                    logger.debug("清理上传目录完成")
                return True, "清理完成"
        except Exception as e:
            logger.error(f"清理失败: {str(e)}")
            return False, f"清理失败: {str(e)}"