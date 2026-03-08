from pydantic import BaseModel

class ServerEntity(BaseModel):
    id: str
    name: str
    # In a real system, this would be a public key
    routing_key: str