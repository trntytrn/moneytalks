from dataclasses import dataclass
from datetime import datetime

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
    password: str
    next_payday: datetime
    payday_frequency: str
    long_term_goal: str
    short_term_goal: str
    # Add other user-related fields as needed
