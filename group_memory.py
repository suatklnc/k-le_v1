import json
import os
import time
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Grup hafıza ayarları
MAX_GROUP_MESSAGES = 50  # Her grup için saklanacak maksimum mesaj sayısı

class GroupMemory:
    def __init__(self):
        self.group_memory_file = "group_messages.json"
        self.group_messages: Dict[str, List[Dict[str, Any]]] = {}
        self._load_group_memory()

    def _load_group_memory(self):
        """Grup mesajlarını dosyadan yükler."""
        if os.path.exists(self.group_memory_file):
            try:
                with open(self.group_memory_file, 'r', encoding='utf-8') as f:
                    self.group_messages = json.load(f)
            except json.JSONDecodeError:
                self.group_messages = {}
                print(f"Warning: Could not decode {self.group_memory_file}. Starting with empty group memory.")
        else:
            self.group_messages = {}

    def _save_group_memory(self):
        """Grup mesajlarını dosyaya kaydeder."""
        with open(self.group_memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.group_messages, f, ensure_ascii=False, indent=4)

    def add_group_message(self, chat_id: int, user_id: int, username: str, message: str):
        """Grup mesajını kaydeder."""
        chat_key = str(chat_id)
        if chat_key not in self.group_messages:
            self.group_messages[chat_key] = []

        # Yeni mesajı ekle
        self.group_messages[chat_key].append({
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        })

        # Maksimum mesaj sayısını kontrol et
        if len(self.group_messages[chat_key]) > MAX_GROUP_MESSAGES:
            self.group_messages[chat_key] = self.group_messages[chat_key][-MAX_GROUP_MESSAGES:]

        self._save_group_memory()

    def get_recent_messages(self, chat_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """Belirli bir süre içindeki mesajları döndürür."""
        chat_key = str(chat_id)
        if chat_key not in self.group_messages:
            return []

        cutoff_time = time.time() - (hours * 3600)
        recent_messages = [
            msg for msg in self.group_messages[chat_key]
            if msg['timestamp'] > cutoff_time
        ]

        return recent_messages

    def get_message_summary(self, chat_id: int, hours: int = 24) -> str:
        """Mesajları özetler."""
        recent_messages = self.get_recent_messages(chat_id, hours)
        
        if not recent_messages:
            return f"Son {hours} saatte hiç mesaj bulunamadı."

        # Mesajları grupla
        user_messages = {}
        for msg in recent_messages:
            username = msg['username'] or f"User_{msg['user_id']}"
            if username not in user_messages:
                user_messages[username] = []
            user_messages[username].append(msg['message'])

        # Özet oluştur
        summary = f"📊 Son {hours} Saatlik Grup Özeti:\n\n"
        summary += f"💬 Toplam mesaj: {len(recent_messages)}\n"
        summary += f"👥 Aktif kullanıcı: {len(user_messages)}\n\n"

        for username, messages in user_messages.items():
            summary += f"👤 {username}: {len(messages)} mesaj\n"

        return summary

    def clear_group_messages(self, chat_id: int):
        """Grup mesajlarını temizler."""
        chat_key = str(chat_id)
        if chat_key in self.group_messages:
            del self.group_messages[chat_key]
            self._save_group_memory()

    def get_group_stats(self) -> Dict[str, Any]:
        """Grup istatistiklerini döndürür."""
        total_groups = len(self.group_messages)
        total_messages = sum(len(msgs) for msgs in self.group_messages.values())
        
        return {
            "total_groups": total_groups,
            "total_messages": total_messages,
            "max_messages_per_group": MAX_GROUP_MESSAGES,
            "groups": list(self.group_messages.keys())
        }

# Global grup hafıza instance'ı
group_memory = GroupMemory()
