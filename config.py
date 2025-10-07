import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Bot ayarları
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
MAX_MESSAGE_LENGTH = 4000
AI_MODEL = "models/gemini-2.0-flash"

# Grup ayarları
ALLOWED_GROUPS = []  # Boş liste tüm grupları kabul eder
ADMIN_USER_IDS = []  # Bot yöneticilerinin user ID'leri

# Hafıza ayarları
MEMORY_ENABLED = True
MAX_MEMORY_MESSAGES = 10  # Her kullanıcı için saklanacak maksimum mesaj sayısı
MEMORY_FILE = "conversation_memory.json"

# Loglama
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
