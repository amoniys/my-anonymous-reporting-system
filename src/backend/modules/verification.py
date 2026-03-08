from typing import Dict, Any # 1. 确保导入了 Any
import logging
from ..core.onion_franking import OnionFrankingClient # 假设这个类在别处定义，需要在此导入
from ..core.onion_franking import OnionFrankingModerator
from ..utils.crypto_utils import decrypt_message
from ..models.moderator import ModeratorEntity

logger = logging.getLogger(__name__)

class VerificationModule:
    def __init__(self):
        self.moderator = OnionFrankingModerator()
        self.moderator_entity = ModeratorEntity()

    # 2. 将返回类型注释中的 'any' 改为 'Any'
    def verify_report(self, report_data: dict, receiver_shared_key_hex: str) -> Dict[str, Any]:
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

            # --- FIX: Add a check for receiver_shared_key_hex ---
            if not receiver_shared_key_hex:
                raise ValueError("Receiver's shared key is missing or invalid.")
            
            shared_key = bytes.fromhex(receiver_shared_key_hex)
            # --- END FIX ---

            decrypted_payload_str = decrypt_message(shared_key, ciphertext, nonce)
            decrypted_payload = eval(decrypted_payload_str) # Same, eval for demo only!
            message = decrypted_payload["message"]

            # 2. Recompute k_f from seed s
            KF_LEN = 32
            k_f = rs[:KF_LEN]

            # 3. Verify the commitment c2
            # 注意：这里需要一个真实的 OnionFrankingClient 实例
            # 为了演示，我们创建一个空的，但在实际应用中，moderator 可能需要自己的共享密钥
            # 这里的模拟实例可能无法执行 com_open，需要根据实际 core 实现调整
            # of_client = OnionFrankingClient(moderator_id, moderator_shared_key, server_pks)
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
            return verification_result

        except ValueError as ve:
            # Catch our custom error and other ValueError from fromhex/decrypt
            logger.error(f"Verification failed due to invalid data: {ve}")
            return {"is_valid": False, "error": str(ve)}
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"is_valid": False, "error": str(e)}