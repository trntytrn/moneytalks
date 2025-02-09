from dataclasses import dataclass

@dataclass
class History:
    user_id: str
    role: str
    content: str

@dataclass
class User:
    user_id: str
    username: str
    email: str
    # Add other user-related fields as needed
