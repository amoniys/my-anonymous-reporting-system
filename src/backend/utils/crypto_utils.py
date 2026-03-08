import hashlib
import hmac
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


def generate_random_key(length: int = 32) -> bytes:
    return secrets.token_bytes(length)

def derive_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password)

def encrypt_message(key: bytes, plaintext: str) -> tuple[bytes, bytes]:
    """使用AES-GCM加密消息"""
    # 1. 创建一个 AESGCM 实例
    aesgcm = AESGCM(key)
    # 2. 手动生成一个 12 字节的随机数 (nonce)
    nonce = secrets.token_bytes(12)
    # 3. 使用该实例进行加密
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return ciphertext, nonce

def decrypt_message(key: bytes, ciphertext: bytes, nonce: bytes) -> str:
    """使用AES-GCM解密消息"""
    # 1. 创建一个 AESGCM 实例
    aesgcm = AESGCM(key)
    # 2. 使用该实例进行解密
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")

def compute_hmac(key: bytes, data: bytes) -> bytes:
    """计算HMAC-SHA256"""
    return hmac.new(key, data, hashlib.sha256).digest()

def verify_hmac(key: bytes, data: bytes, signature: bytes) -> bool:
    """验证HMAC-SHA256"""
    expected_signature = compute_hmac(key, data)
    return hmac.compare_digest(expected_signature, signature)

def hash_data(data: bytes) -> bytes:
    """计算SHA3-256哈希"""
    return hashlib.sha3_256(data).digest()