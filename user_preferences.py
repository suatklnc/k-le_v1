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

    def add_preference(self, chat_id: int, user_id: int, username: str, preference_type: str, preference_value: str, require_consent: bool = True, requesting_user_id: int = None):
        """Kullanıcının tercihini kaydeder."""
        # Güvenlik kontrolü: Sadece kendi tercihlerini kaydedebilir
        if requesting_user_id is not None and requesting_user_id != user_id:
            return False, "❌ Başkasının adına tercih kaydedemezsiniz! Herkes sadece kendi tercihlerini belirleyebilir."
        
        key = self._get_key(chat_id, user_id)
        if key not in self.user_preferences:
            self.user_preferences[key] = {
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "preferences": {},
                "consent_given": False,
                "last_updated": time.time(),
                "created_by": user_id  # Kim oluşturdu
            }

        user_data = self.user_preferences[key]
        
        # Güvenlik kontrolü: Sadece tercih sahibi değiştirebilir
        if "created_by" in user_data and user_data["created_by"] != user_id:
            return False, "❌ Bu kullanıcının tercihlerini değiştirme yetkiniz yok!"
        
        user_data["username"] = username  # Kullanıcı adı güncellenebilir
        
        # Eğer onay gerekiyorsa ve henüz verilmemişse, tercihi kaydetme
        if require_consent and not user_data.get("consent_given", False):
            return False, "Bu tercihi kaydetmek için önce onay vermeniz gerekiyor. 'tercih onayla' komutunu kullanın."
        
        user_data["preferences"][preference_type] = preference_value
        user_data["last_updated"] = time.time()

        self._save_preferences()
        return True, "Tercih başarıyla kaydedildi."

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

    def give_consent(self, chat_id: int, user_id: int, username: str, requesting_user_id: int = None):
        """Kullanıcının tercih kaydetme onayını verir."""
        # Güvenlik kontrolü: Sadece kendi onayını verebilir
        if requesting_user_id is not None and requesting_user_id != user_id:
            return False, "❌ Başkasının adına onay veremezsiniz! Herkes sadece kendi onayını verebilir."
        
        key = self._get_key(chat_id, user_id)
        if key not in self.user_preferences:
            self.user_preferences[key] = {
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "preferences": {},
                "consent_given": True,
                "last_updated": time.time(),
                "created_by": user_id
            }
        else:
            # Güvenlik kontrolü: Sadece tercih sahibi onay verebilir
            if "created_by" in self.user_preferences[key] and self.user_preferences[key]["created_by"] != user_id:
                return False, "❌ Bu kullanıcının adına onay verme yetkiniz yok!"
            
            self.user_preferences[key]["consent_given"] = True
            self.user_preferences[key]["username"] = username
            self.user_preferences[key]["last_updated"] = time.time()
        
        self._save_preferences()
        return True, "Onay başarıyla verildi."

    def revoke_consent(self, chat_id: int, user_id: int, requesting_user_id: int = None):
        """Kullanıcının tercih kaydetme onayını geri alır ve tüm tercihlerini siler."""
        # Güvenlik kontrolü: Sadece kendi onayını geri alabilir
        if requesting_user_id is not None and requesting_user_id != user_id:
            return False, "❌ Başkasının adına onay geri alamazsınız! Herkes sadece kendi onayını geri alabilir."
        
        key = self._get_key(chat_id, user_id)
        if key in self.user_preferences:
            # Güvenlik kontrolü: Sadece tercih sahibi onay geri alabilir
            if "created_by" in self.user_preferences[key] and self.user_preferences[key]["created_by"] != user_id:
                return False, "❌ Bu kullanıcının adına onay geri alma yetkiniz yok!"
            
            self.user_preferences[key]["consent_given"] = False
            self.user_preferences[key]["preferences"] = {}
            self.user_preferences[key]["last_updated"] = time.time()
            self._save_preferences()
        return True, "Onay başarıyla geri alındı."

    def has_consent(self, chat_id: int, user_id: int) -> bool:
        """Kullanıcının tercih kaydetme onayı olup olmadığını kontrol eder."""
        key = self._get_key(chat_id, user_id)
        if key in self.user_preferences:
            return self.user_preferences[key].get("consent_given", False)
        return False

    def validate_preference(self, preference_type: str, preference_value: str) -> tuple[bool, str]:
        """Tercih değerinin geçerli olup olmadığını kontrol eder."""
        # Güvenli tercih türleri
        safe_types = ["hitap", "dil", "ton", "kişilik", "ilgi", "şair"]
        
        if preference_type not in safe_types:
            return False, f"'{preference_type}' güvenli bir tercih türü değil."
        
        # Güvenli değerler
        safe_values = {
            "hitap": ["sen", "siz", "efendim", "kanka", "dost"],
            "dil": ["eski türkçe", "modern türkçe", "arapça", "farsça"],
            "ton": ["şakacı", "ciddi", "romantik", "nazik"],
            "kişilik": ["gururlu", "itaatkar", "şakacı", "saygılı"],
            "ilgi": ["şiir", "müzik", "kitap", "sanat", "edebiyat"],
            "şair": ["nazım hikmet", "yahya kemal", "orhan veli", "cemal süreya", "attila ilhan"]
        }
        
        if preference_type in safe_values:
            if preference_value.lower() not in safe_values[preference_type]:
                return False, f"'{preference_value}' geçerli bir {preference_type} değeri değil."
        
        return True, "Geçerli tercih değeri."

    def get_preferences_stats(self) -> Dict[str, Any]:
        """Tercih istatistiklerini döndürür."""
        total_users = len(self.user_preferences)
        total_preferences = sum(len(user_data["preferences"]) for user_data in self.user_preferences.values())
        users_with_consent = sum(1 for user_data in self.user_preferences.values() if user_data.get("consent_given", False))
        
        return {
            "total_users": total_users,
            "total_preferences": total_preferences,
            "users_with_consent": users_with_consent,
            "users": list(self.user_preferences.keys())
        }

# Global user preferences instance
user_preferences = UserPreferences()
