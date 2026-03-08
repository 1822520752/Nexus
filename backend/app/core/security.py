"""
Nexus 安全模块
提供敏感数据的加密和解密功能（AES-256）
"""
import base64
import os
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings
from app.core.logger import logger


class EncryptionService:
    """
    加密服务类
    
    使用 AES-256 (通过 Fernet) 进行数据加密
    支持密钥派生和安全的密钥管理
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化加密服务
        
        Args:
            secret_key: 加密密钥，如果不提供则从配置或环境变量获取
        """
        # 获取或生成密钥
        self._secret_key = secret_key or self._get_or_create_secret_key()
        self._fernet = self._create_fernet(self._secret_key)
    
    def _get_or_create_secret_key(self) -> str:
        """
        获取或创建加密密钥
        
        Returns:
            加密密钥字符串
        """
        # 尝试从环境变量获取
        key = os.environ.get("NEXUS_SECRET_KEY")
        
        if key:
            return key
        
        # 尝试从密钥文件读取
        key_file = self._get_key_file_path()
        if os.path.exists(key_file):
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    key = f.read().strip()
                    if key:
                        return key
            except Exception as e:
                logger.warning(f"读取密钥文件失败: {e}")
        
        # 生成新的密钥
        key = self._generate_secret_key()
        
        # 保存密钥到文件
        try:
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(key)
            logger.info(f"已生成新的加密密钥并保存到: {key_file}")
        except Exception as e:
            logger.warning(f"保存密钥文件失败: {e}")
        
        return key
    
    def _get_key_file_path(self) -> str:
        """
        获取密钥文件路径
        
        Returns:
            密钥文件的绝对路径
        """
        # 从数据库 URL 中提取数据目录
        db_url = settings.DATABASE_URL
        if ":///" in db_url:
            db_path = db_url.split(":///")[1]
            data_dir = os.path.dirname(db_path)
        else:
            data_dir = "./data"
        
        return os.path.join(data_dir, ".secret_key")
    
    def _generate_secret_key(self) -> str:
        """
        生成安全的随机密钥
        
        Returns:
            Base64 编码的随机密钥
        """
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
    
    def _create_fernet(self, secret_key: str) -> Fernet:
        """
        从密钥创建 Fernet 实例
        
        Args:
            secret_key: 密钥字符串
            
        Returns:
            Fernet 实例
        """
        # 使用 PBKDF2 派生密钥
        salt = b"NexusEncryptionSalt"  # 固定盐值，实际应用中可以存储随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        
        # 派生密钥并创建 Fernet
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            加密后的字符串（Base64 编码）
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: 加密的字符串（Base64 编码）
            
        Returns:
            解密后的明文字符串
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def encrypt_dict(self, data: dict) -> str:
        """
        加密字典数据
        
        Args:
            data: 要加密的字典
            
        Returns:
            加密后的字符串
        """
        import json
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> dict:
        """
        解密字典数据
        
        Args:
            ciphertext: 加密的字符串
            
        Returns:
            解密后的字典
        """
        import json
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)


# 创建全局加密服务实例
encryption_service = EncryptionService()


def encrypt_value(value: str) -> str:
    """
    加密值的便捷函数
    
    Args:
        value: 要加密的值
        
    Returns:
        加密后的值
    """
    return encryption_service.encrypt(value)


def decrypt_value(value: str) -> str:
    """
    解密值的便捷函数
    
    Args:
        value: 要解密的值
        
    Returns:
        解密后的值
    """
    return encryption_service.decrypt(value)
