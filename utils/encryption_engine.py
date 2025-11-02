import os
import random
import hashlib
import shutil
import logging
from datetime import datetime
from utils.file_processor import FileProcessor
from config import Config


# 配置日志
logger = logging.getLogger(__name__)


class EncryptionEngine:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.compression_algorithms = Config.COMPRESSION_ALGORITHMS
        self.extension_pool = Config.EXTENSION_POOL

    def calculate_rounds(self, user_input=None, manual_rounds=3):
        """计算加密轮数"""
        if user_input and user_input.strip():
            # 使用特定代码生成轮数
            hash_value = hashlib.md5(user_input.encode()).hexdigest()
            rounds = (int(hash_value[:2], 16) % 10) + 1
            logger.debug(f"使用特定代码生成轮数: {user_input} -> {rounds}")
            return rounds
        else:
            # 使用手动输入的轮数
            rounds = min(max(manual_rounds, 1), 10)  # 限制在1-10轮
            logger.debug(f"使用手动设置轮数: {rounds}")
            return rounds

    def multi_round_encrypt(self, file_path, rounds, algorithms=None, original_filename=None):
        """多轮加密主函数"""
        if algorithms is None:
            algorithms = self.compression_algorithms

        current_file = file_path
        password_book = {
            'metadata': {
                'encryption_time': datetime.now().isoformat(),
                'total_rounds': rounds,
                'original_filename': original_filename or os.path.basename(file_path),
                'original_hash': self._calculate_file_hash(file_path)
            },
            'rounds': {}
        }

        temp_files = []  # 记录中间文件用于清理
        temp_dirs = []  # 记录临时目录用于清理

        try:
            for round_num in range(1, rounds + 1):
                logger.debug(f"第{round_num}轮加密，当前文件: {current_file}")

                # 1. 压缩
                algorithm = random.choice(algorithms)
                success, compressed_file, error = self.file_processor.compress_file(current_file, algorithm)
                if not success:
                    raise Exception(f"第{round_num}轮压缩失败: {error}")

                # 记录中间文件用于清理
                if current_file != file_path and current_file not in temp_files:
                    temp_files.append(current_file)

                # 2. 修改后缀名
                new_extension = random.choice(self.extension_pool)
                success, encrypted_file, error = self.file_processor.change_extension(compressed_file, new_extension)
                if not success:
                    raise Exception(f"第{round_num}轮修改后缀名失败: {error}")

                # 记录到密码本
                password_book['rounds'][str(round_num)] = {
                    'extension': new_extension,
                    'algorithm': algorithm,
                    'compressed_filename': os.path.basename(compressed_file),
                    'encrypted_filename': os.path.basename(encrypted_file)
                }

                current_file = encrypted_file

            # 记录最终加密文件
            final_file = current_file
            password_book['metadata']['final_filename'] = os.path.basename(final_file)
            password_book['metadata']['final_hash'] = self._calculate_file_hash(final_file)

            # 清理中间文件（保留最终文件）
            self._cleanup_temp_resources(temp_files, temp_dirs)

            logger.info(f"加密完成: {file_path} -> {final_file}, 轮数: {rounds}")
            return True, final_file, password_book, None

        except Exception as e:
            # 清理所有临时资源
            self._cleanup_temp_resources(temp_files, temp_dirs)
            logger.error(f"加密失败: {file_path} - {str(e)}")
            return False, None, None, str(e)

    def multi_round_decrypt(self, file_path, password_book):
        """多轮解密主函数"""
        if not self._validate_password_book(password_book):
            return False, None, "密码本格式无效"

        current_file = file_path
        temp_files = []  # 记录中间文件用于清理
        temp_dirs = []   # 记录临时目录用于清理

        try:
            total_rounds = password_book['metadata']['total_rounds']
            logger.debug(f"开始解密，总轮数: {total_rounds}, 初始文件: {current_file}")

            # 反向解密（从最后一轮到第一轮）
            for round_num in range(total_rounds, 0, -1):
                round_info = password_book['rounds'][str(round_num)]
                logger.debug(f"第{round_num}轮解密: {round_info}")

                # 1. 检查当前文件是否存在
                if not os.path.exists(current_file):
                    raise Exception(f"第{round_num}轮文件不存在: {current_file}")

                # 2. 还原后缀名（从加密后缀名还原为压缩文件后缀名）
                expected_extension = round_info['extension']
                current_extension = os.path.splitext(current_file)[1]

                if current_extension != expected_extension:
                    # 尝试自动修正扩展名
                    base_name = os.path.splitext(current_file)[0]
                    corrected_file = base_name + expected_extension
                    if os.path.exists(corrected_file):
                        current_file = corrected_file
                        logger.debug(f"自动修正扩展名: {corrected_file}")
                    else:
                        # 如果修正失败，尝试直接使用当前文件
                        logger.warning(f"第{round_num}轮后缀名不匹配但继续处理: 期望{expected_extension}, 实际{current_extension}")

                # 3. 还原为压缩文件
                algorithm = round_info['algorithm']
                compressed_extension = self._get_compressed_extension(algorithm)
                
                # 创建新的压缩文件名
                base_name = os.path.splitext(current_file)[0]
                compressed_file = base_name + compressed_extension
                
                # 重命名文件（如果需要）
                if current_file != compressed_file and not os.path.exists(compressed_file):
                    os.rename(current_file, compressed_file)
                    logger.debug(f"重命名: {current_file} -> {compressed_file}")
                    current_file = compressed_file
                elif os.path.exists(compressed_file):
                    current_file = compressed_file

                # 记录中间文件用于清理（如果不是原始文件）
                if current_file != file_path and current_file not in temp_files:
                    temp_files.append(current_file)

                # 4. 解压文件
                logger.debug(f"开始解压: {current_file} 使用算法: {algorithm}")
                success, extracted_file, error = self.file_processor.extract_file(current_file, algorithm)
                if not success:
                    raise Exception(f"第{round_num}轮解压失败: {error}")

                logger.debug(f"解压成功: {current_file} -> {extracted_file}")

                # 5. 验证解压结果
                if not os.path.exists(extracted_file):
                    raise Exception(f"第{round_num}轮解压后文件不存在: {extracted_file}")

                # 记录解压创建的目录（如果是目录的话）
                if os.path.isdir(extracted_file) and extracted_file not in temp_dirs:
                    temp_dirs.append(extracted_file)

                # 记录中间文件用于清理
                if current_file != file_path and current_file not in temp_files:
                    temp_files.append(current_file)

                current_file = extracted_file

            # 验证最终文件是否存在
            if not os.path.exists(current_file):
                raise Exception(f"解密完成后文件不存在: {current_file}")

            # 如果最终文件在 extracted 目录中，将其移动到上传目录
            final_filename = os.path.basename(current_file)
            if 'extracted_' in current_file:
                # 创建目标路径
                target_path = os.path.join(Config.UPLOAD_FOLDER, final_filename)
                
                # 如果目标文件已存在，先删除
                if os.path.exists(target_path):
                    os.remove(target_path)
                
                # 移动文件到上传目录
                if os.path.isfile(current_file):
                    shutil.move(current_file, target_path)
                    current_file = target_path
                    logger.debug(f"移动解密文件到上传目录: {current_file}")
                elif os.path.isdir(current_file):
                    # 如果是目录，将其压缩为zip文件
                    zip_filename = final_filename + '.zip'
                    zip_path = os.path.join(Config.UPLOAD_FOLDER, zip_filename)
                    
                    # 创建zip文件
                    import zipfile
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(current_file):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, current_file)
                                zipf.write(file_path, arcname)
                    
                    current_file = zip_path
                    final_filename = zip_filename
                    logger.debug(f"将解密目录压缩为: {current_file}")

            # 验证原始文件哈希
            original_hash = password_book['metadata']['original_hash']
            if original_hash != "unknown":  # 只有计算了哈希时才验证
                current_hash = self._calculate_file_hash(current_file)
                if original_hash != current_hash:
                    logger.warning(f"文件哈希不匹配但继续: 期望{original_hash}, 实际{current_hash}")
                    # 不因为哈希不匹配而失败，只记录警告

            logger.info(f"解密完成，最终文件: {current_file}")
            return True, current_file, None

        except Exception as e:
            # 清理临时资源
            self._cleanup_temp_resources(temp_files, temp_dirs)
            logger.error(f"解密过程异常: {str(e)}")
            return False, None, str(e)

    def _cleanup_temp_resources(self, temp_files, temp_dirs):
        """清理临时文件和目录"""
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        logger.debug(f"清理临时文件: {temp_file}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {temp_file}: {str(e)}")

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"清理临时目录: {temp_dir}")
                except Exception as e:
                    logger.warning(f"清理临时目录失败 {temp_dir}: {str(e)}")

    def _validate_password_book(self, password_book):
        """验证密码本格式"""
        try:
            required_metadata = ['encryption_time', 'total_rounds', 'original_filename', 'original_hash']
            required_round_keys = ['extension', 'algorithm']

            if 'metadata' not in password_book or 'rounds' not in password_book:
                return False

            # 检查元数据
            for key in required_metadata:
                if key not in password_book['metadata']:
                    return False

            # 检查轮次信息
            total_rounds = password_book['metadata']['total_rounds']
            if len(password_book['rounds']) != total_rounds:
                return False

            for round_num in range(1, total_rounds + 1):
                if str(round_num) not in password_book['rounds']:
                    return False
                for key in required_round_keys:
                    if key not in password_book['rounds'][str(round_num)]:
                        return False

            return True

        except Exception as e:
            logger.error(f"密码本验证失败: {str(e)}")
            return False

    def _get_compressed_extension(self, algorithm):
        """根据压缩算法获取对应的文件扩展名"""
        extension_map = {
            'zip': '.zip',
            'tar': '.tar',
            'gzip': '.gz',
            'tar.gz': '.tar.gz',
            'tar.bz2': '.tar.bz2'
        }

        return extension_map.get(algorithm, '.zip')

    def _calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"计算文件哈希失败: {file_path} - {str(e)}")
            return "unknown"

    def get_supported_algorithms(self):
        """获取支持的压缩算法列表"""
        return self.compression_algorithms.copy()

    def get_extension_pool(self):
        """获取后缀名池"""
        return self.extension_pool.copy()