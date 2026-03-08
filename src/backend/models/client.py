from pydantic import BaseModel, Field
from typing import Optional
from ..utils.crypto_utils import generate_random_key

def generate_shared_key_hex():
    """生成一个新的32字节密钥并转换为十六进制字符串"""
    return generate_random_key(32).hex()

class ClientEntity(BaseModel):
    id: str
    name: str
    # 使用 Field 和 default_factory 确保该字段始终有值
    shared_key_with_receiver: str = Field(default_factory=generate_shared_key_hex)
    credential_count: int = 0
