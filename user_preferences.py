import json
import os
import time
from typing import Dict, List, Any

USER_PREFERENCES_FILE = "user_preferences.json"

class UserPreferences:
    def __init__(self):
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self._load_preferences()

    def _load_preferences(self):
        """Kullanıcı tercihlerini dosyadan yükler."""
        if os.path.exists(USER_PREFERENCES_FILE):
            try:
                with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            except json.JSONDecodeError:
                self.user_preferences = {}
                print(f"Warning: Could not decode {USER_PREFERENCES_FILE}. Starting with empty preferences.")
        else:
            self.user_preferences = {}

    def _save_preferences(self):
        """Kullanıcı tercihlerini dosyaya kaydeder."""
        with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, ensure_ascii=False, indent=4)

    def _get_key(self, chat_id: int, user_id: int) -> str:
        """Chat ve user ID'sine göre benzersiz anahtar oluşturur."""
        return f"{chat_id}_{user_id}"

    def add_preference(self, chat_id: int, user_id: int, username: str, preference_type: str, preference_value: str):
        """Kullanıcının tercihini kaydeder."""
        key = self._get_key(chat_id, user_id)
        if key not in self.user_preferences:
            self.user_preferences[key] = {
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "preferences": {},
                "last_updated": time.time()
            }

        user_data = self.user_preferences[key]
        user_data["username"] = username  # Kullanıcı adı güncellenebilir
        user_data["preferences"][preference_type] = preference_value
        user_data["last_updated"] = time.time()

        self._save_preferences()

    def get_user_preferences(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        """Belirli bir kullanıcının tercihlerini döndürür."""
        key = self._get_key(chat_id, user_id)
        return self.user_preferences.get(key, {})

    def get_chat_users_preferences(self, chat_id: int) -> List[Dict[str, Any]]:
        """Belirli bir chat'teki tüm kullanıcıların tercihlerini döndürür."""
        users_preferences = []
        for key, user_data in self.user_preferences.items():
            if user_data["chat_id"] == chat_id:
                users_preferences.append({
                    "user_id": user_data["user_id"],
                    "username": user_data["username"],
                    "preferences": user_data["preferences"],
                    "last_updated": user_data["last_updated"]
                })
        return users_preferences

    def update_preference(self, chat_id: int, user_id: int, username: str, preference_type: str, preference_value: str):
        """Mevcut tercihi günceller."""
        self.add_preference(chat_id, user_id, username, preference_type, preference_value)

    def remove_preference(self, chat_id: int, user_id: int, preference_type: str):
        """Belirli bir tercihi siler."""
        key = self._get_key(chat_id, user_id)
        if key in self.user_preferences and preference_type in self.user_preferences[key]["preferences"]:
            del self.user_preferences[key]["preferences"][preference_type]
            self.user_preferences[key]["last_updated"] = time.time()
            self._save_preferences()

    def clear_user_preferences(self, chat_id: int, user_id: int):
        """Belirli bir kullanıcının tüm tercihlerini siler."""
        key = self._get_key(chat_id, user_id)
        if key in self.user_preferences:
            del self.user_preferences[key]
            self._save_preferences()

    def clear_chat_preferences(self, chat_id: int):
        """Belirli bir chat'teki tüm kullanıcı tercihlerini siler."""
        keys_to_delete = [key for key, user_data in self.user_preferences.items() if user_data["chat_id"] == chat_id]
        for key in keys_to_delete:
            del self.user_preferences[key]
        self._save_preferences()

    def get_preferences_stats(self) -> Dict[str, Any]:
        """Tercih istatistiklerini döndürür."""
        total_users = len(self.user_preferences)
        total_preferences = sum(len(user_data["preferences"]) for user_data in self.user_preferences.values())
        
        return {
            "total_users": total_users,
            "total_preferences": total_preferences,
            "users": list(self.user_preferences.keys())
        }

# Global user preferences instance
user_preferences = UserPreferences()
