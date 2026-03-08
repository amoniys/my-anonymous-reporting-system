from typing import Dict, Any
import logging
from ..core.onion_franking import OnionFrankingClient, OnionFrankingModerator
from ..utils.crypto_utils import decrypt_message
from ..models.moderator import ModeratorEntity
from ..core.ws_manager import manager # 导入 WebSocket 管理器

logger = logging.getLogger(__name__)

class VerificationModule:
    def __init__(self):
        self.moderator = OnionFrankingModerator()
        self.moderator_entity = ModeratorEntity()

    async def verify_report(self, report_data: dict, receiver_shared_key_hex: str) -> Dict[str, Any]:
        try:
            c1_hex = report_data["c1_encrypted_msg"]
            c2_hex = report_data["c2_commitment"]
            context = report_data["context"]
            s_hex = report_data["s_seed"]
            rs_hex = report_data["rs_randomness"]

            c1 = bytes.fromhex(c1_hex)
            c2 = bytes.fromhex(c2_hex)
            s = bytes.fromhex(s_hex)
            rs = bytes.fromhex(rs_hex)

            # 1. Decrypt the main message and seed using the receiver's key
            c1_parsed = eval(c1.decode('utf-8')) # Note: Use only for demo, never in production!
            ciphertext = bytes.fromhex(c1_parsed["ciphertext"])
            nonce = bytes.fromhex(c1_parsed["nonce"])

            if not receiver_shared_key_hex:
                raise ValueError("Receiver's shared key is missing or invalid.")
            
            shared_key = bytes.fromhex(receiver_shared_key_hex)

            decrypted_payload_str = decrypt_message(shared_key, ciphertext, nonce)
            decrypted_payload = eval(decrypted_payload_str) # Same, eval for demo only!
            message = decrypted_payload["message"]

            # 2. Recompute k_f from seed s
            # --- 修正：KF_LEN 应与 OnionFrankingClient 中定义的一致 ---
            # 从 OnionFrankingClient 的 send_online 方法中可以看到 KF_LEN = 32
            KF_LEN = 32 
            k_f = rs[:KF_LEN] # rs 的前 KF_LEN 个字节就是 k_f
            # --- END FIX ---

            # 3. Verify the commitment c2
            # 创建一个临时的 Client 实例来调用其 com_open 方法
            of_client = OnionFrankingClient("", b"", [])
            is_commitment_valid = of_client.com_open(c2, message.encode('utf-8'), k_f)

            # 4. Generate sigma and sigma_c using the moderator's key
            sigma, sigma_c_computed = self.moderator.mod_process(c2, context)

            # 5. Prepare data for final check (usually done by the storage module or another service)
            verification_result = {
                "is_valid": is_commitment_valid,
                "message_content": message,
                "original_context": context,
                "franking_evidence": {
                    "sigma": sigma.hex(),
                    "sigma_c": sigma_c_computed.hex(),
                    "k_f_used": k_f.hex(),
                    "c2_commitment": c2.hex(),
                },
                "sender_identity": "Anonymized (Verification Successful)" # The core point: sender ID is not revealed
            }
            logger.info(f"Report verified successfully. Message: '{message}'")

            # --- 新增：发送验证结果到 WebSocket 客户端 ---
            await manager.broadcast({
                "type": "verification_result",
                "payload": verification_result
            })
            # --- END NEW CODE ---

            return verification_result

        except ValueError as ve:
            logger.error(f"Verification failed due to invalid data: {ve}")
            error_result = {"is_valid": False, "error": str(ve)}
            await manager.broadcast({
                "type": "verification_result",
                "payload": error_result
            })
            return error_result
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            error_result = {"is_valid": False, "error": str(e)}
            await manager.broadcast({
                "type": "verification_result",
                "payload": error_result
            })
            return error_result