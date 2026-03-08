from pydantic import BaseModel

class ModeratorEntity(BaseModel):
    id: str = "moderator_1"
    name: str = "Content Moderator"
    # In a real system, this would be a public key
    verification_key: str = "predefined_verification_key_for_demo"