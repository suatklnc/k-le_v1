import json
import os
import time
from typing import Dict, List, Any
from config import MEMORY_FILE, MAX_MEMORY_MESSAGES, MEMORY_ENABLED

class ConversationMemory:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.load_memory()
    
    def load_memory(self):
        """Hafızayı dosyadan yükle"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
            else:
                self.conversations = {}
        except Exception as e:
            print(f"Hafıza yükleme hatası: {e}")
            self.conversations = {}
    
    def save_memory(self):
        """Hafızayı dosyaya kaydet"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Hafıza kaydetme hatası: {e}")
    
    def get_conversation_key(self, user_id: int, chat_id: int) -> str:
        """Konuşma anahtarı oluştur"""
        return f"{user_id}_{chat_id}"
    
    def add_message(self, user_id: int, chat_id: int, role: str, content: str):
        """Mesajı hafızaya ekle"""
        if not MEMORY_ENABLED:
            return
            
        key = self.get_conversation_key(user_id, chat_id)
        
        if key not in self.conversations:
            self.conversations[key] = []
        
        # Yeni mesajı ekle
        self.conversations[key].append({
            "role": role,
            "content": content,
            "timestamp": str(time.time())
        })
        
        # Maksimum mesaj sayısını kontrol et
        if len(self.conversations[key]) > MAX_MEMORY_MESSAGES:
            self.conversations[key] = self.conversations[key][-MAX_MEMORY_MESSAGES:]
        
        self.save_memory()
    
    def get_conversation_history(self, user_id: int, chat_id: int) -> List[Dict[str, str]]:
        """Konuşma geçmişini al"""
        if not MEMORY_ENABLED:
            return []
            
        key = self.get_conversation_key(user_id, chat_id)
        return self.conversations.get(key, [])
    
    def clear_conversation(self, user_id: int, chat_id: int):
        """Konuşma geçmişini temizle"""
        key = self.get_conversation_key(user_id, chat_id)
        if key in self.conversations:
            del self.conversations[key]
            self.save_memory()
    
    def clear_all_memory(self):
        """Tüm hafızayı temizle"""
        self.conversations = {}
        self.save_memory()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Hafıza istatistiklerini al"""
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv) for conv in self.conversations.values())
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "memory_enabled": MEMORY_ENABLED,
            "max_messages_per_conversation": MAX_MEMORY_MESSAGES
        }

# Global hafıza instance'ı
memory = ConversationMemory()
