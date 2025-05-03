# utils/state_manager.py

USER_STATE = {}  # Словник для зберігання станів користувачів

def set_state(user_id, state):
    USER_STATE[user_id] = state

def get_state(user_id):
    return USER_STATE.get(user_id)

def clear_state(user_id):
    if user_id in USER_STATE:
        del USER_STATE[user_id]