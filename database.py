import json
import os
from openpyxl import load_workbook

class Database:
    def __init__(self):
        self.users_file = "data/users_data/users.json"
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w") as f:
                json.dump({}, f)
    
    def save_user(self, user_id, user_data):
        with open(self.users_file, "r") as f:
            users = json.load(f)
        users[str(user_id)] = user_data
        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=2)
    
    def get_user_data(self, user_id):
        xlsx_path = f"data/users_data/{user_id}/data.xlsx"
        if os.path.exists(xlsx_path):
            return load_workbook(xlsx_path)
        return None 