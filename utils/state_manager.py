# utils/state_manager.py

# Dictionary to keep track of user states 
USER_STATE = {}

def set_state(user_id, state):
    """Sets the state for a specific user."""
    USER_STATE[user_id] = state

def get_state(user_id):
    """Gets the current state of a user. Returns None if no state is set."""
    return USER_STATE.get(user_id)

def clear_state(user_id):
    """Clears (removes) the state for a specific user."""
    if user_id in USER_STATE:
        del USER_STATE[user_id]