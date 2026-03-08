import json
import hashlib
from typing import List, Tuple
from ..utils.crypto_utils import generate_random_key, encrypt_message, decrypt_message, compute_hmac, verify_hmac, hash_data
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Constants for the scheme
SIGMA_C_LENGTH = 32  # Length for sigma_c in bytes
SIGMA_LENGTH = 32    # Length for sigma in bytes
COMMITMENT_LENGTH = 64 # Length for commitment in bytes

class OnionFrankingClient:
    def __init__(self, client_id: str, shared_key_with_receiver: bytes, server_public_keys: List[bytes]):
        self.uid = client_id
        self.k_r = shared_key_with_receiver
        self.pks = server_public_keys

    def send_preprocessing(self, num_servers: int) -> Tuple[bytes, bytes, bytes]:
        """离线阶段准备数据"""
        s = generate_random_key(32)
        KF_LEN = 32
        MRT_LEN = 128 + 10 # Empirical value based on Rust code
        rs_size = KF_LEN + MRT_LEN * num_servers
        rs = generate_random_key(rs_size)

        c3 = b""
        # 逆序遍历，模拟洋葱封装
        for i in reversed(range(num_servers)):
            r_i = rs[KF_LEN + i * MRT_LEN : KF_LEN + (i + 1) * MRT_LEN]
            payload = json.dumps({"c3": c3.hex(), "r_i": r_i.hex()}).encode('utf-8')
            # 这里简化为直接加密，实际应使用非对称加密库
            c3 = self._simple_encrypt(payload, self.pks[i])
        
        return s, rs, c3

    def _simple_encrypt(self, data: bytes, key: bytes) -> bytes:
        # 简化的加密模拟，实际应用需替换为非对称加密
        return compute_hmac(key[:32], data)

    def send_online(self, message: str, s: bytes, rs: bytes) -> Tuple[bytes, bytes]:
        """在线阶段发送消息"""
        KF_LEN = 32
        k_f = rs[:KF_LEN]
        c2 = self.com_commit(k_f, message.encode('utf-8'))
        ciphertext, nonce = encrypt_message(self.k_r, json.dumps({"message": message, "s": s.hex()}))
        c1 = json.dumps({"ciphertext": ciphertext.hex(), "nonce": nonce.hex()}).encode('utf-8')
        return c1, c2

    def com_commit(self, key: bytes, message: bytes) -> bytes:
        """承诺函数 (HMAC)"""
        return compute_hmac(key, message)

    def com_open(self, commitment: bytes, message: bytes, key: bytes) -> bool:
        """打开承诺 (验证)"""
        return verify_hmac(key, message, commitment)


class OnionFrankingModerator:
    def __init__(self):
        self.k_m = generate_random_key(32)

    def mod_process(self, c2: bytes, ctx: str) -> Tuple[bytes, bytes]:
        """审核员处理，生成签名和哈希"""
        sigma = compute_hmac(self.k_m, c2 + ctx.encode('utf-8'))
        sigma_c = hash_data(sigma + c2 + ctx.encode('utf-8'))
        return sigma, sigma_c

    def moderate(self, message: str, ctx: str, rd: Tuple[bytes, bytes], sigma: bytes) -> bool:
        """审核验证"""
        k_f, c2 = rd
        valid_f = OnionFrankingClient("", b"", []).com_open(c2, message.encode('utf-8'), k_f)
        valid_r = verify_hmac(self.k_m, c2 + ctx.encode('utf-8'), sigma)
        return valid_f and valid_r

# --- 新增：服务器密钥生成函数 ---
def generate_server_keys(num_servers: int = 3) -> Tuple[List[bytes], List[bytes]]:
    """
    Generates public keys for servers in the onion franking system.
    This function creates elliptic curve key pairs for each server.
    """
    public_keys = []
    private_keys = []
    for i in range(num_servers):
        # Generate a private key for the server
        private_key = ec.generate_private_key(ec.SECP256R1())
        # Derive the public key from the private key
        public_key = private_key.public_key()
        
        # Serialize keys to bytes for easy handling
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_keys.append(public_pem)
        private_keys.append(private_pem)
        
    return public_keys, private_keys
# --- END NEW CODE ---