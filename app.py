from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
import uuid
import logging
import re
from werkzeug.utils import secure_filename
from config import Config
from utils.file_processor import FileProcessor
from utils.encryption_engine import EncryptionEngine
from utils.password_book import PasswordBookManager

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化组件
file_processor = FileProcessor()
encryption_engine = EncryptionEngine()
password_book_manager = PasswordBookManager()

# 会话管理（简化版）
sessions = {}


def get_session():
    """获取或创建会话"""
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            'uploaded_files': [],
            'password_books': [],
            'created_time': os.times().elapsed
        }
    return session_id, sessions[session_id]


def find_matching_password_book(encrypted_filename, password_books_dict):
    """查找与加密文件匹配的密码本"""
    encrypted_base = os.path.splitext(encrypted_filename)[0]
    logger.debug(f"开始匹配密码本，加密文件: {encrypted_filename}, 基础名: {encrypted_base}")

    for pb_filename, pb_data in password_books_dict.items():
        # 获取密码本中记录的原始文件名
        original_filename = pb_data.get('metadata', {}).get('original_filename', '')
        original_base = os.path.splitext(original_filename)[0] if original_filename else ''

        # 获取密码本中记录的最终加密文件名
        final_filename = pb_data.get('metadata', {}).get('final_filename', '')
        final_base = os.path.splitext(final_filename)[0] if final_filename else ''

        logger.debug(f"检查密码本: {pb_filename}, 原始文件: {original_filename}, 最终文件: {final_filename}")

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
            match_filename_prefix(encrypted_base, original_base),
        ]

        # 检查是否有任何匹配
        if any(matches):
            logger.debug(f"匹配成功! 匹配条件: {matches}")
            return pb_filename, pb_data

    logger.debug("所有匹配策略都失败了")
    return None, None


def match_filename_prefix(encrypted_base, original_base):
    """通过文件名前缀匹配"""
    if not original_base:
        return False

    # 移除常见的时间戳前缀
    encrypted_clean = remove_timestamp_prefix(encrypted_base)
    original_clean = remove_timestamp_prefix(original_base)

    return encrypted_clean == original_clean


def remove_timestamp_prefix(filename):
    """移除时间戳前缀"""
    # 匹配常见的时间戳格式：20241102_143000_ 或 20241102143000_
    pattern = r'^\d{8}_\d{6}_|\d{14}_'
    return re.sub(pattern, '', filename)


def simple_password_book_match(encrypted_filename, password_books_dict):
    """简单的密码本匹配逻辑"""
    encrypted_base = os.path.splitext(encrypted_filename)[0]

    for pb_filename, pb_data in password_books_dict.items():
        pb_original_name = pb_data.get('metadata', {}).get('original_filename', '')
        pb_original_base = os.path.splitext(pb_original_name)[0] if pb_original_name else ''

        # 简单的包含匹配
        if (encrypted_base in pb_original_base or
                pb_original_base in encrypted_base or
                encrypted_base in pb_filename):
            return pb_data

    return None


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/upload', methods=['GET'])
def upload_redirect():
    """上传页面重定向到加密页面"""
    return redirect(url_for('encrypt_config'))


@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt_config():
    """加密配置页面"""
    session_id, session = get_session()

    if request.method == 'POST':
        # 检查是否有新文件上传或会话中已有文件
        uploaded_files = []

        # 检查是否有新文件上传
        if 'files' in request.files:
            files = request.files.getlist('files')

            for file in files:
                if file.filename == '':
                    continue

                # 验证文件
                is_valid, message = file_processor.validate_file(file.filename)
                if not is_valid:
                    flash(f"{file.filename}: {message}", 'error')
                    continue

                # 保存文件
                success, filepath, filename = file_processor.save_uploaded_file(file)
                if success:
                    file_info = file_processor.get_file_info(filepath)
                    uploaded_files.append({
                        'filepath': filepath,
                        'filename': filename,
                        'original_name': file.filename,
                        'size': file_info['size'] if file_info else 0
                    })
                    flash(f"{file.filename} 上传成功", 'success')
                else:
                    flash(f"{file.filename} 上传失败: {filename}", 'error')

        # 如果没有新文件上传，检查会话中是否有已上传的文件
        if not uploaded_files and session['uploaded_files']:
            uploaded_files = session['uploaded_files']

        # 如果仍然没有文件，显示错误
        if not uploaded_files:
            flash('请选择文件或确保文件已成功上传', 'error')
            return redirect(request.url)

        # 更新会话（如果有新文件上传）
        if 'files' in request.files and uploaded_files:
            session['uploaded_files'] = uploaded_files

        # 获取加密参数
        rounds_method = request.form.get('rounds_method', 'manual')
        manual_rounds = int(request.form.get('manual_rounds', 3))
        specific_code = request.form.get('specific_code', '').strip()
        encrypt_password_book = request.form.get('encrypt_password_book') == 'on'
        password = request.form.get('password', '')

        # 计算加密轮数
        if rounds_method == 'specific_code' and specific_code:
            rounds = encryption_engine.calculate_rounds(user_input=specific_code)
        else:
            rounds = encryption_engine.calculate_rounds(manual_rounds=manual_rounds)

        # 处理每个文件
        results = []
        for file_info in session['uploaded_files']:
            try:
                # 执行加密
                success, encrypted_file, password_book, error = encryption_engine.multi_round_encrypt(
                    file_info['filepath'],
                    rounds,
                    original_filename=file_info['original_name']
                )
                if success:
                    # 生成密码本
                    success_pb, password_book_data, book_id = password_book_manager.generate_password_book({
                        'metadata': password_book['metadata'],
                        'rounds': password_book['rounds']
                    })
                    if success_pb:
                        # 加密密码本（如果需要）
                        if encrypt_password_book and password:
                            success_enc, encrypted_pb, error_enc = password_book_manager.encrypt_password_book(
                                password_book_data, password
                            )
                            if success_enc:
                                password_book_data = encrypted_pb

                        # 保存密码本
                        success_save, pb_filepath, pb_filename = password_book_manager.save_password_book(
                            password_book_data)

                        if success_save:
                            results.append({
                                'original_file': file_info['original_name'],
                                'encrypted_file': os.path.basename(encrypted_file),
                                'encrypted_filepath': encrypted_file,
                                'password_book': pb_filename,
                                'password_bookpath': pb_filepath,
                                'rounds': rounds,
                                'success': True
                            })
                            # 更新会话
                            session['password_books'].append({
                                'filename': pb_filename,
                                'filepath': pb_filepath,
                                'original_file': file_info['original_name']
                            })
                        else:
                            results.append({
                                'original_file': file_info['original_name'],
                                'success': False,
                                'error': f'保存密码本失败: {pb_filename}'
                            })
                    else:
                        results.append({
                            'original_file': file_info['original_name'],
                            'success': False,
                            'error': f'生成密码本失败: {book_id}'
                        })
                else:
                    results.append({
                        'original_file': file_info['original_name'],
                        'success': False,
                        'error': error
                    })

            except Exception as e:
                results.append({
                    'original_file': file_info['original_name'],
                    'success': False,
                    'error': str(e)
                })

        # 清理上传的原始文件
        file_paths = [file_info['filepath'] for file_info in session['uploaded_files']]
        file_processor.cleanup_temp_files(file_paths)
        session['uploaded_files'] = []
        return render_template('result.html', results=results, operation='encrypt')

    # 如果没有上传文件，显示提示信息
    if not session['uploaded_files']:
        flash('请先上传文件再进行加密操作', 'info')

    return render_template('encrypt.html',
                           files=session['uploaded_files'],
                           algorithms=encryption_engine.get_supported_algorithms())


@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt_config():
    """解密配置页面"""
    session_id, session = get_session()

    if request.method == 'POST':
        # 检查文件上传
        if 'encrypted_files' not in request.files:
            flash('请选择加密文件', 'error')
            return redirect(request.url)

        if 'password_books' not in request.files:
            flash('请选择密码本文件', 'error')
            return redirect(request.url)

        encrypted_files = request.files.getlist('encrypted_files')
        password_books = request.files.getlist('password_books')
        decrypt_password = request.form.get('decrypt_password', '')

        # 保存上传的加密文件
        uploaded_files = []
        for file in encrypted_files:
            if file.filename and file.filename != '':
                success, filepath, filename = file_processor.save_uploaded_file(file)
                if success:
                    uploaded_files.append({
                        'filepath': filepath,
                        'filename': filename,
                        'original_name': file.filename
                    })
                    logger.debug(f"成功上传加密文件: {file.filename}")
                else:
                    flash(f'文件 {file.filename} 上传失败: {filename}', 'error')

        # 保存上传的密码本文件
        password_book_data = {}
        password_book_files = {}  # 存储密码本文件名和文件路径的映射

        for pb_file in password_books:
            if pb_file.filename and pb_file.filename != '':
                success, filepath, filename = file_processor.save_uploaded_file(pb_file)
                if success:
                    # 加载密码本
                    success_load, password_book, error = password_book_manager.load_password_book(filepath)
                    if success_load:
                        # 解密密码本（如果需要）
                        if password_book.get('encrypted'):
                            if not decrypt_password:
                                flash(f'{pb_file.filename}: 密码本已加密，请输入密码', 'error')
                                continue
                            success_dec, decrypted_pb, error_dec = password_book_manager.decrypt_password_book(
                                password_book, decrypt_password
                            )
                            if success_dec:
                                password_book = decrypted_pb
                                logger.debug(f"成功解密密码本: {pb_file.filename}")
                            else:
                                flash(f'{pb_file.filename}: {error_dec}', 'error')
                                continue

                        # 存储密码本数据
                        password_book_data[pb_file.filename] = password_book
                        password_book_files[pb_file.filename] = filepath
                        logger.debug(f"成功加载密码本: {pb_file.filename}")
                    else:
                        flash(f'{pb_file.filename}: {error}', 'error')
                        logger.error(f"加载密码本失败: {pb_file.filename} - {error}")
                else:
                    flash(f'密码本 {pb_file.filename} 上传失败', 'error')

        # 检查是否有可用的密码本
        if not password_book_data:
            flash('没有可用的密码本文件，请检查文件格式或密码', 'error')
            # 清理上传的文件
            file_paths = [file_info['filepath'] for file_info in uploaded_files]
            file_paths.extend(password_book_files.values())
            file_processor.cleanup_temp_files(file_paths)
            return redirect(request.url)

        # 检查是否有可用的加密文件
        if not uploaded_files:
            flash('没有可用的加密文件', 'error')
            # 清理上传的密码本
            file_paths = list(password_book_files.values())
            file_processor.cleanup_temp_files(file_paths)
            return redirect(request.url)

        logger.debug(f"开始解密处理，加密文件数量: {len(uploaded_files)}, 密码本数量: {len(password_book_data)}")

        # 执行解密
        results = []
        for file_info in uploaded_files:
            logger.debug(f"处理加密文件: {file_info['original_name']}")

            # 改进的密码本匹配逻辑
            matched_pb = None
            matched_pb_filename = None

            # 方法1: 使用增强的匹配逻辑
            matched_pb_filename, matched_pb = find_matching_password_book(
                file_info['original_name'], password_book_data
            )

            # 方法2: 如果增强匹配失败，使用简单匹配
            if not matched_pb:
                matched_pb = simple_password_book_match(file_info['original_name'], password_book_data)
                if matched_pb:
                    for pb_filename, pb_data in password_book_data.items():
                        if pb_data == matched_pb:
                            matched_pb_filename = pb_filename
                            break

            # 方法3: 单文件单密码本情况
            if not matched_pb and len(uploaded_files) == 1 and len(password_book_data) == 1:
                matched_pb_filename = list(password_book_data.keys())[0]
                matched_pb = password_book_data[matched_pb_filename]
                flash(f'使用唯一的密码本 {matched_pb_filename} 进行解密尝试', 'info')
                logger.info(f"使用唯一密码本: {matched_pb_filename}")

            if not matched_pb:
                error_msg = f'未找到匹配的密码本。文件: {file_info["original_name"]}，可用密码本: {", ".join(password_book_data.keys())}'
                results.append({
                    'encrypted_file': file_info['original_name'],
                    'success': False,
                    'error': error_msg
                })
                logger.warning(error_msg)
                continue

            logger.debug(f"匹配成功: {file_info['original_name']} -> {matched_pb_filename}")

            try:
                # 检查加密文件是否存在
                if not os.path.exists(file_info['filepath']):
                    raise Exception(f"加密文件不存在: {file_info['filepath']}")

                # 执行解密
                success, decrypted_file, error = encryption_engine.multi_round_decrypt(
                    file_info['filepath'], matched_pb
                )
                if success:
                    # 检查解密后的文件是否存在
                    if not os.path.exists(decrypted_file):
                        raise Exception(f"解密后的文件不存在: {decrypted_file}")

                    results.append({
                        'encrypted_file': file_info['original_name'],
                        'decrypted_file': os.path.basename(decrypted_file),
                        'decrypted_filepath': decrypted_file,
                        'original_filename': matched_pb['metadata']['original_filename'],
                        'success': True
                    })
                    logger.info(f"解密成功: {file_info['original_name']}")
                else:
                    results.append({
                        'encrypted_file': file_info['original_name'],
                        'success': False,
                        'error': error
                    })
                    logger.error(f"解密失败: {file_info['original_name']} - {error}")
            except Exception as e:
                error_msg = f'解密过程异常: {str(e)}'
                results.append({
                    'encrypted_file': file_info['original_name'],
                    'success': False,
                    'error': error_msg
                })
                logger.error(f"解密异常: {file_info['original_name']} - {str(e)}")

        # 清理上传的文件
        file_paths = [file_info['filepath'] for file_info in uploaded_files]
        file_paths.extend(password_book_files.values())
        file_processor.cleanup_temp_files(file_paths)

        return render_template('result.html', results=results, operation='decrypt')

    return render_template('decrypt.html')


@app.route('/password_books', methods=['GET'])
def password_books():
    """密码本管理页面"""
    success, books, error = password_book_manager.list_password_books()
    if not success:
        flash(f'获取密码本列表失败: {error}', 'error')
        books = []
    return render_template('password_books.html', password_books=books)


@app.route('/download/<file_type>/<filename>')
def download_file(file_type, filename):
    """文件下载"""
    try:
        if file_type == 'encrypted':
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        elif file_type == 'password_book':
            filepath = os.path.join('static/password_books', filename)
        elif file_type == 'decrypted':
            # 解密后的文件可能在 UPLOAD_FOLDER 或其中的子目录中
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            
            # 如果文件不存在于根目录，尝试在 _extracted 目录中查找
            if not os.path.exists(filepath):
                # 搜索所有可能的解密文件位置
                for root, dirs, files in os.walk(Config.UPLOAD_FOLDER):
                    if filename in files:
                        filepath = os.path.join(root, filename)
                        break
                else:
                    # 如果还是找不到，尝试使用基础名称搜索
                    base_name = os.path.splitext(filename)[0]
                    for root, dirs, files in os.walk(Config.UPLOAD_FOLDER):
                        for file in files:
                            if base_name in file:
                                filepath = os.path.join(root, file)
                                filename = file  # 更新下载的文件名
                                break
        else:
            flash('无效的文件类型', 'error')
            return redirect(url_for('index'))
        
        if os.path.exists(filepath):
            # 确保文件名是安全的
            safe_filename = secure_filename(os.path.basename(filepath))
            logger.debug(f"下载文件: {filepath} -> {safe_filename}")
            return send_file(
                filepath, 
                as_attachment=True,
                download_name=safe_filename
            )
        else:
            logger.error(f"文件不存在: {filepath}")
            flash(f'文件不存在: {filename}', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"下载失败: {str(e)}")
        flash(f'下载失败: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/delete_password_book/<filename>')
def delete_password_book(filename):
    """删除密码本"""
    success, message = password_book_manager.delete_password_book(filename)
    if success:
        flash(f'密码本 {filename} 删除成功', 'success')
    else:
        flash(f'删除失败: {message}', 'error')
    return redirect(url_for('password_books'))


@app.errorhandler(413)
def too_large(e):
    """文件过大错误处理"""
    flash('文件大小超过限制（最大500MB）', 'error')
    return redirect(request.url)


@app.errorhandler(404)
def not_found(e):
    """404错误处理"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """500错误处理"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    # 确保静态目录存在
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/password_books', exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)