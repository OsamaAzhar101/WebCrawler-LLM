from pydantic import BaseModel


class Business(BaseModel):
    """
    Represents the data structure of a Business.
    """
    name: str
    address: str
    phone: str
    email: str