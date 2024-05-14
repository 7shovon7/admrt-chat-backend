def generate_conversation_id(user1: str, user2: str):
    users = sorted([user1.strip().lower(), user2.strip().lower()])
    return '-'.join(users)
