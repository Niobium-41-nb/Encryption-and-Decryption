import json
import os
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class PasswordBookManager:
    def __init__(self):
        self.storage_dir = 'static/password_books'
        os.makedirs(self.storage_dir, exist_ok=True)

    def generate_password_book(self, encryption_data):
        """生成密码本"""
        try:
            password_book = {
                'metadata': encryption_data['metadata'], 
                'rounds': encryption_data['rounds'], 
                'version': '1.0', 
                'generator': 'Flask File Encryption System' 
            }

            # 生成密码本ID
            book_id = self._generate_book_id(password_book)
            password_book['metadata']['book_id'] = book_id

            return True, password_book, book_id

        except Exception as e:
            return False, None, f"生成密码本失败: {str(e)}"

    def save_password_book(self, password_book, filename=None):
        """保存密码本到文件"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_name = password_book['metadata']['original_filename']
                book_id = password_book['metadata']['book_id']
                filename = f"{timestamp}_{original_name}_{book_id[:8]}.json"

            filepath = os.path.join(self.storage_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(password_book, f, ensure_ascii=False, indent=2)

            return True, filepath, filename

        except Exception as e:
            return False, None, f"保存密码本失败: {str(e)}"

    def load_password_book(self, file_path):
        """从文件加载密码本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                password_book = json.load(f)

            # 验证密码本格式
            if not self._validate_password_book_format(password_book):
                return False, None, "密码本格式无效"

            return True, password_book, None

        except Exception as e:
            return False, None, f"加载密码本失败: {str(e)}"

    def encrypt_password_book(self, password_book, password):
        """加密密码本"""
        try:
            # 生成密钥
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)

            # 加密密码本数据
            password_book_str = json.dumps(password_book)
            encrypted_data = fernet.encrypt(password_book_str.encode())

            # 创建加密后的密码本
            encrypted_book = {
                'encrypted': True,
                'salt': base64.urlsafe_b64encode(salt).decode(),
                'data': base64.urlsafe_b64encode(encrypted_data).decode(),
                'version': '1.0'
            }
            return True, encrypted_book, None

        except Exception as e:
            return False, None, f"加密密码本失败: {str(e)}"

    def decrypt_password_book(self, encrypted_book, password):
        """解密密码本"""
        try:
            if not encrypted_book.get('encrypted'):
                return False, None, "密码本未加密"

            # 还原盐值
            salt = base64.urlsafe_b64decode(encrypted_book['salt'])

            # 生成密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)

            # 解密数据
            encrypted_data = base64.urlsafe_b64decode(encrypted_book['data'])
            decrypted_data = fernet.decrypt(encrypted_data)
            password_book = json.loads(decrypted_data.decode())

            return True, password_book, None

        except Exception as e:
            return False, None, f"解密密码本失败: 密码可能错误"

    def merge_password_books(self, books_dict):
        """合并多个密码本"""
        try:
            merged_book = {
                'metadata': {
                    'merge_time': datetime.now().isoformat(),
                    'total_files': len(books_dict),
                    'files': {}
                },
                'books': {}
            }

            for filename, password_book in books_dict.items():
                book_id = password_book["metadata"]['book_id']
                merged_book['books'][book_id] = {
                    'filename': filename,
                    'original_filename': password_book["metadata"]['original_filename'],
                    'encryption_time': password_book["metadata"]['encryption_time'], 
                    'total_rounds': password_book["metadata"]['total_rounds'], 
                    'rounds': password_book["rounds"]
                }
                merged_book["metadata"]['files'][book_id] = filename

            return True, merged_book, None

        except Exception as e:
            return False, None, f"合并密码本失败: {str(e)}"

    def list_password_books(self):
        """列出所有密码本文件"""
        try:
            books = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.storage_dir, filename)
                    stat = os.stat(filepath)

                    books.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'created_time': datetime.fromtimestamp(stat.st_ctime)
                    })
            return True, books, None

        except Exception as e:
            return False, None, f"列出密码本失败: {str(e)}"

    def delete_password_book(self, filename):
        """删除密码本文件"""
        try:
            filepath = os.path.join(self.storage_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, "删除成功"
            else:
                return False, "文件不存在"

        except Exception as e:
            return False, f"删除失败: {str(e)}"

    def _generate_book_id(self, password_book):
        """生成密码本唯一ID"""
        data_str = json.dumps(password_book, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def _validate_password_book_format(self, password_book):
        """验证密码本格式"""
        try:
            required_keys = ['metadata', 'rounds', 'version']
            required_metadata = ['encryption_time', 'total_rounds', 'original_filename', 'original_hash']

            # 检查必需键
            for key in required_keys:
                if key not in password_book:
                    return False

            # 检查元数据
            for key in required_metadata:
                if key not in password_book['metadata']:
                    return False

            # 检查轮次信息
            total_rounds = password_book['metadata']['total_rounds']
            if len(password_book['rounds']) != total_rounds:
                return False

            return True

        except:
            return False

    def cleanup_old_books(self, hours=24):
        """清理旧的密码本文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            deleted_count = 0

            for filename in os.listdir(self.storage_dir):
                filepath = os.path.join(self.storage_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    if stat.st_mtime < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1

            return True, f"清理了 {deleted_count} 个旧密码本"

        except Exception as e:
            return False, f"清理失败: {str(e)}"


def find_matching_password_book(self, encrypted_filename, password_books_dict):
    """查找与加密文件匹配的密码本"""
    encrypted_base = os.path.splitext(encrypted_filename)[0]

    for pb_filename, pb_data in password_books_dict.items():
        # 获取密码本中记录的原始文件名
        original_filename = pb_data.get('metadata', {}).get('original_filename', '')
        original_base = os.path.splitext(original_filename)[0] if original_filename else ''

        # 获取密码本中记录的最终加密文件名
        final_filename = pb_data.get('metadata', {}).get('final_filename', '')
        final_base = os.path.splitext(final_filename)[0] if final_filename else ''

        # 多种匹配策略
        matches = [
            # 加密文件名与密码本记录的最终文件名匹配
            encrypted_filename == final_filename,
            encrypted_base == final_base,

            # 加密文件名包含原始文件名（常见命名模式）
            original_base in encrypted_filename if original_base else False,

            # 密码本文件名包含加密文件名或原始文件名
            encrypted_base in pb_filename,
            original_base in pb_filename if original_base else False,

            # 文件名前缀匹配（去除时间戳等前缀）
            self._match_filename_prefix(encrypted_base, original_base),

            # 文件哈希匹配（最准确但需要计算）
            self._match_by_file_hash(encrypted_filename, pb_data)
        ]

        if any(matches):
            return pb_filename, pb_data

    return None, None


def _match_filename_prefix(self, encrypted_base, original_base):
    """通过文件名前缀匹配"""
    if not original_base:
        return False

    # 移除常见的时间戳前缀
    encrypted_clean = self._remove_timestamp_prefix(encrypted_base)
    original_clean = self._remove_timestamp_prefix(original_base)

    return encrypted_clean == original_clean


def _remove_timestamp_prefix(self, filename):
    """移除时间戳前缀"""
    import re
    # 匹配常见的时间戳格式：20241102_143000_ 或 20241102143000_
    pattern = r'^\d{8}_\d{6}_|\d{14}_'
    return re.sub(pattern, '', filename)


def _match_by_file_hash(self, encrypted_filename, password_book_data):
    """通过文件哈希匹配（最准确但需要计算文件哈希）"""
    try:
        # 获取密码本中记录的最终文件哈希
        expected_hash = password_book_data.get('metadata', {}).get('final_hash')
        if not expected_hash or expected_hash == 'unknown':
            return False

        # 计算当前加密文件的哈希
        from utils.encryption_engine import EncryptionEngine
        engine = EncryptionEngine()
        actual_hash = engine._calculate_file_hash(encrypted_filename)

        return actual_hash == expected_hash
    except:
        return False