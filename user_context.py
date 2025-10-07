import json
import os
import time
from typing import Dict, List, Any

# Kullanıcı bağlam dosyası
USER_CONTEXT_FILE = "user_context.json"
MAX_USER_MESSAGES = 20  # Her kullanıcı için saklanacak maksimum mesaj sayısı

class UserContext:
    def __init__(self):
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        self._load_user_context()

    def _load_user_context(self):
        """Kullanıcı bağlamını dosyadan yükler."""
        if os.path.exists(USER_CONTEXT_FILE):
            try:
                with open(USER_CONTEXT_FILE, 'r', encoding='utf-8') as f:
                    self.user_contexts = json.load(f)
            except json.JSONDecodeError:
                self.user_contexts = {}
                print(f"Warning: Could not decode {USER_CONTEXT_FILE}. Starting with empty user context.")
        else:
            self.user_contexts = {}

    def _save_user_context(self):
        """Kullanıcı bağlamını dosyaya kaydeder."""
        with open(USER_CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.user_contexts, f, ensure_ascii=False, indent=4)

    def add_user_message(self, chat_id: int, user_id: int, username: str, message: str):
        """Kullanıcının mesajını bağlamına ekler."""
        chat_id_str = str(chat_id)
        user_id_str = str(user_id)
        
        if chat_id_str not in self.user_contexts:
            self.user_contexts[chat_id_str] = {}
        
        if user_id_str not in self.user_contexts[chat_id_str]:
            self.user_contexts[chat_id_str][user_id_str] = {
                "username": username,
                "messages": [],
                "last_seen": time.time()
            }
        
        # Yeni mesajı ekle
        self.user_contexts[chat_id_str][user_id_str]["messages"].append({
            "message": message,
            "timestamp": time.time()
        })
        
        # Son görülme zamanını güncelle
        self.user_contexts[chat_id_str][user_id_str]["last_seen"] = time.time()
        
        # Maksimum mesaj sayısını kontrol et
        if len(self.user_contexts[chat_id_str][user_id_str]["messages"]) > MAX_USER_MESSAGES:
            self.user_contexts[chat_id_str][user_id_str]["messages"] = \
                self.user_contexts[chat_id_str][user_id_str]["messages"][-MAX_USER_MESSAGES:]
        
        self._save_user_context()

    def get_user_recent_messages(self, chat_id: int, user_id: int, count: int = 5) -> List[Dict[str, Any]]:
        """Belirli bir kullanıcının son mesajlarını döndürür."""
        chat_id_str = str(chat_id)
        user_id_str = str(user_id)
        
        if chat_id_str not in self.user_contexts:
            return []
        
        if user_id_str not in self.user_contexts[chat_id_str]:
            return []
        
        messages = self.user_contexts[chat_id_str][user_id_str]["messages"]
        return messages[-count:] if messages else []

    def get_user_info(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        """Kullanıcı bilgilerini döndürür."""
        chat_id_str = str(chat_id)
        user_id_str = str(user_id)
        
        if chat_id_str not in self.user_contexts:
            return {}
        
        if user_id_str not in self.user_contexts[chat_id_str]:
            return {}
        
        return self.user_contexts[chat_id_str][user_id_str]

    def search_users_by_name(self, chat_id: int, name_query: str) -> List[Dict[str, Any]]:
        """İsim ile kullanıcı arama."""
        chat_id_str = str(chat_id)
        
        if chat_id_str not in self.user_contexts:
            return []
        
        matching_users = []
        name_query_lower = name_query.lower()
        
        for user_id_str, user_data in self.user_contexts[chat_id_str].items():
            username = user_data.get("username", "").lower()
            if name_query_lower in username:
                matching_users.append({
                    "user_id": int(user_id_str),
                    "username": user_data.get("username", ""),
                    "last_seen": user_data.get("last_seen", 0),
                    "message_count": len(user_data.get("messages", []))
                })
        
        return matching_users

    def get_chat_users_summary(self, chat_id: int) -> List[Dict[str, Any]]:
        """Chat'teki tüm kullanıcıların özetini döndürür."""
        chat_id_str = str(chat_id)
        
        if chat_id_str not in self.user_contexts:
            return []
        
        users_summary = []
        for user_id_str, user_data in self.user_contexts[chat_id_str].items():
            users_summary.append({
                "user_id": int(user_id_str),
                "username": user_data.get("username", ""),
                "last_seen": user_data.get("last_seen", 0),
                "message_count": len(user_data.get("messages", [])),
                "last_message": user_data.get("messages", [])[-1]["message"] if user_data.get("messages") else ""
            })
        
        # Son görülme zamanına göre sırala
        users_summary.sort(key=lambda x: x["last_seen"], reverse=True)
        return users_summary

    def clear_user_context(self, chat_id: int, user_id: int = None):
        """Kullanıcı bağlamını temizler."""
        chat_id_str = str(chat_id)
        
        if chat_id_str not in self.user_contexts:
            return
        
        if user_id is None:
            # Tüm kullanıcıları temizle
            del self.user_contexts[chat_id_str]
        else:
            # Belirli kullanıcıyı temizle
            user_id_str = str(user_id)
            if user_id_str in self.user_contexts[chat_id_str]:
                del self.user_contexts[chat_id_str][user_id_str]
        
        self._save_user_context()

    def get_user_context_stats(self) -> Dict[str, Any]:
        """Kullanıcı bağlam istatistiklerini döndürür."""
        total_chats = len(self.user_contexts)
        total_users = sum(len(users) for users in self.user_contexts.values())
        total_messages = sum(
            sum(len(user_data.get("messages", [])) for user_data in users.values())
            for users in self.user_contexts.values()
        )
        
        return {
            "total_chats": total_chats,
            "total_users": total_users,
            "total_messages": total_messages,
            "max_messages_per_user": MAX_USER_MESSAGES
        }

user_context = UserContext()
