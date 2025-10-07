import logging
import asyncio
from typing import List, Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import google.generativeai as genai
from config import *
from group_memory import group_memory
from user_preferences import user_preferences

# Loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Google Gemini istemcisini başlat
genai.configure(api_key=GEMINI_API_KEY)

class TelegramAIBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Bot komutlarını ve mesaj işleyicilerini ayarla"""
        # Komut işleyicileri
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("memory", self.memory_command))
        self.application.add_handler(CommandHandler("clear", self.clear_memory_command))
        self.application.add_handler(CommandHandler("groupinfo", self.group_info_command))
        self.application.add_handler(CommandHandler("ozet", self.summary_command))
        self.application.add_handler(CommandHandler("temizle", self.clear_group_command))
        self.application.add_handler(CommandHandler("uyeler", self.users_command))
        
        # Mesaj işleyicileri
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bot başlatma komutu"""
        welcome_message = """
🤖 Selamün aleyküm! Ben mahzen grubunun şahsi kölesiyim.

📝 Hizmetlerim:
• Sorularınıza yapay zeka ile cevap veririm
• Grup sohbetlerinde aktifim
• Komutlarım: /help, /status

💡 Nasıl kullanılır:
Sadece bana bir mesaj gönderin, size hizmet etmeye çalışacağım!

⚠️ Not: Gururlu, şakacı ve edebi bir köleyim! Bazen eski Türkçe konuşur, bazen şiirle cevap veririm!
        """
        await update.message.reply_text(welcome_message)
        logger.info(f"Start command used by {update.effective_user.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yardım komutu"""
        help_text = """
🤖 **MAHZEN GRUBU ŞAHSİ KÖLESİ - YARDIM**

📚 **TEMEL KOMUTLAR:**
/start - Botu başlat ve hoş geldin mesajı
/help - Bu yardım menüsünü göster
/status - Bot durumunu ve kimliğini kontrol et
/memory - Hafıza durumunu göster
/clear - Konuşma geçmişini temizle

📊 **GRUP KOMUTLARI:**
/groupinfo - Grup bilgilerini göster
/ozet - Son 24 saatlik konuşmaları özetle
/temizle - Grup mesajlarını temizle
/uyeler - Grup üyelerinin durumunu göster

🔐 **TERCİH YÖNETİMİ (Kişisel Otonomi):**
`tercih onayla` - Tercih kaydetme onayını ver
`tercih kaydet [tip]: [değer]` - Yeni tercih kaydet
`tercih durumum` - Tercih durumunu görüntüle
`tercihlerim` - Kayıtlı tercihlerini görüntüle
`tercih sil [tip]` - Belirli tercihi sil
`tercih onayı geri al` - Onayı geri al ve tercihleri sil
`tercih yardım` - Detaylı tercih yardımı

🎯 **GÜVENLİ TERCIH TÜRLERİ:**
• **hitap**: sen, siz, efendim, kanka, dost
• **dil**: eski türkçe, modern türkçe, arapça, farsça
• **ton**: şakacı, ciddi, romantik, nazik
• **kişilik**: gururlu, itaatkar, şakacı, saygılı
• **ilgi**: şiir, müzik, kitap, sanat, edebiyat
• **şair**: nazım hikmet, yahya kemal, orhan veli, vb.

🛡️ **GÜVENLİK VE GİZLİLİK:**
✅ **Kişisel Otonomi**: Herkes sadece kendi tercihlerini belirleyebilir
✅ **Başkası Adına Karar Verme Engelleme**: Hiç kimse başkasının adına tercih kaydedemez
✅ **Açık Onay Sistemi**: Tercih kaydetmek için kullanıcı onayı gerekli
✅ **Kimlik Doğrulama**: Her işlem sadece tercih sahibi tarafından yapılabilir
✅ **Gizlilik**: Sadece onay veren kullanıcıların tercihleri kaydedilir

💬 **KULLANIM:**
• Herhangi bir soru sorabilirsiniz
• Grup sohbetlerinde @bot_username ile etiketleyin
• Bot'a yanıt vererek mesaj gönderin
• Yapay zeka ile en iyi cevabı almaya çalışırım

🧠 **HAFIZA SİSTEMİ:**
• Konuşma geçmişinizi hatırlar
• Grup üyelerinin son mesajlarını takip eder
• Kişisel tercihlerinizi uygular
• Daha iyi ve kişiselleştirilmiş yanıtlar verir

⚠️ **ÖNEMLİ NOTLAR:**
• Gururlu, şakacı ve edebi bir köleyim
• Bazen eski Türkçe konuşur, bazen şiirle cevap veririm
• Her kullanıcının kimlik haklarına saygı gösteririm
• Sadece mahzen grubunda aktifim
        """
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bot durumu komutu"""
        status_text = f"""
🤖 Bot Durumu: Aktif
📊 Model: {AI_MODEL} (Google Gemini)
👤 Kullanıcı: {update.effective_user.first_name}
🆔 User ID: {update.effective_user.id}
🏠 Kimlik: Mahzen grubunun edebi kölesi
💪 Kişilik: Gururlu, şakacı ve edebi
📚 Özellikler: Eski Türkçe, şiirler, şakalar
        """
        await update.message.reply_text(status_text)
    
    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hafıza durumu komutu"""
        stats = group_memory.get_group_stats()
        user_id = update.effective_user.id
        chat_id = update.message.chat.id
        
        # Grup ve özel mesaj konuşmalarını al
        if chat_id < 0:  # Grup mesajı
            user_conversation = group_memory.get_conversation_history(chat_id, user_id)
            private_conversation = group_memory.get_private_conversation_history(user_id)
            conversation_type = "Grup"
        else:  # Özel mesaj
            user_conversation = group_memory.get_private_conversation_history(user_id)
            private_conversation = []
            conversation_type = "Özel"
        
        memory_text = f"""
🧠 Hafıza Durumu:
📊 Toplam grup: {stats['total_groups']}
💬 Toplam grup mesajı: {stats['total_messages']}
📝 Maksimum mesaj/grup: {stats['max_messages_per_group']}

👤 Sizin {conversation_type.lower()} konuşmanız:
📨 Mesaj sayısı: {len(user_conversation)}
🆔 User ID: {user_id}
💬 Chat ID: {chat_id}

🔒 Özel mesajlarınız:
📨 Mesaj sayısı: {len(private_conversation)}
        """
        await update.message.reply_text(memory_text)
    
    async def clear_memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hafıza temizleme komutu"""
        user_id = update.effective_user.id
        chat_id = update.message.chat.id
        
        # Grup ve özel mesajları temizle
        if chat_id < 0:  # Grup mesajı
            group_memory.clear_user_messages(chat_id, user_id)
            group_memory.clear_private_messages(user_id)
            await update.message.reply_text("🧹 Grup ve özel mesaj geçmişiniz temizlendi!")
        else:  # Özel mesaj
            group_memory.clear_private_messages(user_id)
            await update.message.reply_text("🧹 Özel mesaj geçmişiniz temizlendi!")
        
        logger.info(f"Memory cleared for user {user_id} in chat {chat_id}")
    
    async def group_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Grup bilgi komutu"""
        chat_type = update.message.chat.type
        chat_id = update.message.chat.id
        bot_username = context.bot.username
        
        info_text = f"""
📊 Grup Bilgileri:
💬 Chat Tipi: {chat_type}
🆔 Chat ID: {chat_id}
🤖 Bot Kullanıcı Adı: @{bot_username}

📝 Grup Kullanımı:
• @{bot_username} merhaba
• Bot'a yanıt vererek mesaj gönder
• /groupinfo - Bu bilgileri göster

🔧 Grup Ayarları:
• Bot'u gruba admin yapın
• Mesaj gönderme izni verin
        """
        await update.message.reply_text(info_text)

    async def summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Grup mesajlarını özetleme komutu"""
        chat_id = update.message.chat.id

        # Sadece gruplarda çalışır
        if update.message.chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("Bu komut sadece gruplarda çalışır!")
            return

        # Güvenlik kontrolü
        if ALLOWED_GROUPS and chat_id not in ALLOWED_GROUPS:
            logger.warning(f"Unauthorized summary command attempt: {chat_id} by user {update.effective_user.id}")
            return

        # Son 24 saatlik özet
        recent_messages = group_memory.get_recent_messages(chat_id, 24)
        if recent_messages:
            # AI ile gerçek özet oluştur
            ai_summary = await self.create_ai_summary(recent_messages)
            await update.message.reply_text(ai_summary)
        else:
            await update.message.reply_text("Son 24 saatte hiç mesaj bulunamadı.")
        logger.info(f"Summary requested by {update.effective_user.id} in chat {chat_id}")

    async def clear_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Grup mesajlarını temizleme komutu"""
        chat_id = update.message.chat.id

        # Sadece gruplarda çalışır
        if update.message.chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("Bu komut sadece gruplarda çalışır!")
            return

        # Güvenlik kontrolü
        if ALLOWED_GROUPS and chat_id not in ALLOWED_GROUPS:
            logger.warning(f"Unauthorized clear command attempt: {chat_id} by user {update.effective_user.id}")
            return

        group_memory.clear_group_messages(chat_id)
        await update.message.reply_text("🧹 Grup mesajları temizlendi!")
        logger.info(f"Group messages cleared by {update.effective_user.id} in chat {chat_id}")

    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Grup üyelerinin durumunu gösteren komut"""
        chat_id = update.message.chat.id

        # Sadece gruplarda çalışır
        if update.message.chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("Bu komut sadece gruplarda çalışır!")
            return

        # Güvenlik kontrolü
        if ALLOWED_GROUPS and chat_id not in ALLOWED_GROUPS:
            logger.warning(f"Unauthorized users command attempt: {chat_id} by user {update.effective_user.id}")
            return

        # Son 24 saatlik mesajlardan kullanıcı özetini oluştur
        recent_messages = group_memory.get_recent_messages(chat_id, 24)
        
        if not recent_messages:
            await update.message.reply_text("Henüz grup üyelerinin mesajları kaydedilmemiş.")
            return
        
        # Kullanıcıları grupla ve istatistiklerini hesapla
        user_stats = {}
        for msg in recent_messages:
            user_id = msg['user_id']
            username = msg['username']
            
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'username': username,
                    'message_count': 0,
                    'last_message': '',
                    'last_timestamp': 0
                }
            
            user_stats[user_id]['message_count'] += 1
            
            # En son mesajı güncelle
            if msg['timestamp'] > user_stats[user_id]['last_timestamp']:
                user_stats[user_id]['last_message'] = msg['message']
                user_stats[user_id]['last_timestamp'] = msg['timestamp']
        
        # En aktif 10 kullanıcıyı göster
        sorted_users = sorted(user_stats.values(), key=lambda x: x['last_timestamp'], reverse=True)[:10]
        
        users_text = "👥 Grup Üyelerinin Durumu:\n\n"
        for i, user_info in enumerate(sorted_users, 1):
            username = user_info["username"]
            message_count = user_info["message_count"]
            last_message = user_info["last_message"][:50] + "..." if len(user_info["last_message"]) > 50 else user_info["last_message"]
            
            users_text += f"{i}. **{username}**\n"
            users_text += f"   📨 Mesaj sayısı: {message_count}\n"
            users_text += f"   💬 Son mesaj: {last_message}\n\n"
        
        await update.message.reply_text(users_text)
        logger.info(f"Users command used by {update.effective_user.id} in chat {chat_id}")
    
    async def handle_preference_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, user_id: int, chat_id: int, username: str):
        """Kullanıcı tercih komutlarını işler"""
        try:
            message_lower = message.lower()
            
            # Bot adını temizle
            bot_username = context.bot.username
            if bot_username:
                if message.startswith(f'@{bot_username}'):
                    message = message.replace(f'@{bot_username}', '').strip()
                elif message.startswith(f'/{bot_username}'):
                    message = message.replace(f'/{bot_username}', '').strip()
            
            # Tercih kaydetme komutları
            if "tercih kaydet" in message_lower or "preference save" in message_lower:
                # Format: "tercih kaydet [tip]: [değer]"
                parts = message.split(":", 1)
                if len(parts) == 2:
                    pref_type = parts[0].replace("tercih kaydet", "").replace("preference save", "").strip()
                    pref_value = parts[1].strip()
                    
                    if pref_type and pref_value:
                        # Tercih değerini doğrula
                        is_valid, validation_msg = user_preferences.validate_preference(pref_type, pref_value)
                        if not is_valid:
                            await update.message.reply_text(f"❌ {validation_msg}")
                            return
                        
                        # Tercihi kaydet (onay kontrolü ile)
                        success, result_msg = user_preferences.add_preference(chat_id, user_id, username, pref_type, pref_value, requesting_user_id=user_id)
                        if success:
                            await update.message.reply_text(f"✅ Tercih kaydedildi: **{pref_type}** = {pref_value}")
                            logger.info(f"Preference saved: {pref_type}={pref_value} for user {user_id} in chat {chat_id}")
                        else:
                            await update.message.reply_text(f"⚠️ {result_msg}")
                    else:
                        await update.message.reply_text("❌ Format: `tercih kaydet [tip]: [değer]`")
                else:
                    await update.message.reply_text("❌ Format: `tercih kaydet [tip]: [değer]`")
            
            elif "tercih sil" in message_lower or "preference delete" in message_lower:
                # Format: "tercih sil [tip]"
                parts = message.split()
                if len(parts) >= 3:
                    pref_type = " ".join(parts[2:]).strip()
                    user_preferences.remove_preference(chat_id, user_id, pref_type)
                    await update.message.reply_text(f"🗑️ Tercih silindi: **{pref_type}**")
                    logger.info(f"Preference deleted: {pref_type} for user {user_id} in chat {chat_id}")
                else:
                    await update.message.reply_text("❌ Format: `tercih sil [tip]`")
            
            elif "tercihlerim" in message_lower or "my preferences" in message_lower:
                # Kullanıcının tercihlerini göster
                user_prefs = user_preferences.get_user_preferences(chat_id, user_id)
                if user_prefs and "preferences" in user_prefs and user_prefs["preferences"]:
                    prefs_text = f"📋 **{username}**'nin tercihleri:\n\n"
                    for pref_type, pref_value in user_prefs["preferences"].items():
                        prefs_text += f"• **{pref_type}**: {pref_value}\n"
                    await update.message.reply_text(prefs_text)
                else:
                    await update.message.reply_text(f"📋 **{username}**, henüz tercih kaydetmemişsin.")
            
            elif "tercih onayla" in message_lower or "preference consent" in message_lower:
                # Kullanıcının tercih kaydetme onayını ver
                success, result_msg = user_preferences.give_consent(chat_id, user_id, username, requesting_user_id=user_id)
                if success:
                    await update.message.reply_text("✅ Tercih kaydetme onayınız verildi! Artık tercihlerinizi kaydedebilirim.")
                    logger.info(f"Consent given by user {user_id} in chat {chat_id}")
                else:
                    await update.message.reply_text(f"❌ {result_msg}")
            
            elif "tercih onayı geri al" in message_lower or "revoke consent" in message_lower:
                # Kullanıcının tercih kaydetme onayını geri al
                success, result_msg = user_preferences.revoke_consent(chat_id, user_id, requesting_user_id=user_id)
                if success:
                    await update.message.reply_text("🗑️ Tercih kaydetme onayınız geri alındı ve tüm tercihleriniz silindi.")
                    logger.info(f"Consent revoked by user {user_id} in chat {chat_id}")
                else:
                    await update.message.reply_text(f"❌ {result_msg}")
            
            elif "tercih durumum" in message_lower or "preference status" in message_lower:
                # Kullanıcının tercih durumunu göster
                has_consent = user_preferences.has_consent(chat_id, user_id)
                user_prefs = user_preferences.get_user_preferences(chat_id, user_id)
                
                status_text = f"📋 **{username}**'nin tercih durumu:\n\n"
                status_text += f"🔐 Onay durumu: {'✅ Verildi' if has_consent else '❌ Verilmedi'}\n"
                
                if user_prefs and "preferences" in user_prefs and user_prefs["preferences"]:
                    status_text += f"\n📝 Kayıtlı tercihler:\n"
                    for pref_type, pref_value in user_prefs["preferences"].items():
                        status_text += f"• **{pref_type}**: {pref_value}\n"
                else:
                    status_text += "\n📝 Henüz kayıtlı tercih yok."
                
                await update.message.reply_text(status_text)
            
            elif "tercih yardım" in message_lower or "preference help" in message_lower:
                help_text = """📋 **Tercih Komutları:**

• `tercih onayla` - Tercih kaydetme onayını ver
• `tercih onayı geri al` - Onayı geri al ve tercihleri sil
• `tercih durumum` - Tercih durumunu görüntüle
• `tercih kaydet [tip]: [değer]` - Yeni tercih kaydet
• `tercih sil [tip]` - Tercih sil
• `tercihlerim` - Tercihlerini görüntüle
• `tercih yardım` - Bu yardımı göster

**Güvenli Tercih Türleri:**
• **hitap**: sen, siz, efendim, kanka, dost
• **dil**: eski türkçe, modern türkçe, arapça, farsça
• **ton**: şakacı, ciddi, romantik, nazik
• **kişilik**: gururlu, itaatkar, şakacı, saygılı
• **ilgi**: şiir, müzik, kitap, sanat, edebiyat
• **şair**: nazım hikmet, yahya kemal, orhan veli, cemal süreya, attila ilhan

**Örnekler:**
• `tercih kaydet hitap: sen` (bana "sen" diye hitap et)
• `tercih kaydet dil: eski türkçe` (eski Türkçe kullan)
• `tercih kaydet ton: şakacı` (şakacı ol)

**Gizlilik:** Tercihlerinizi kaydetmek için önce `tercih onayla` komutunu kullanın."""
                await update.message.reply_text(help_text)
            
        except Exception as e:
            logger.error(f"Error handling preference command: {e}")
            await update.message.reply_text("❌ Tercih komutu işlenirken hata oluştu.")
    
    async def auto_detect_preferences(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, user_id: int, chat_id: int, username: str):
        """Kullanıcı mesajlarından otomatik tercih algılar"""
        try:
            message_lower = message.lower()
            
            # Bot adını temizle
            bot_username = context.bot.username
            if bot_username:
                if message.startswith(f'@{bot_username}'):
                    message = message.replace(f'@{bot_username}', '').strip()
                elif message.startswith(f'/{bot_username}'):
                    message = message.replace(f'/{bot_username}', '').strip()
            
            message_lower = message.lower()
            detected_preferences = []
            
            # Hitap tercihleri
            if any(word in message_lower for word in ['bana', 'sen', 'siz', 'hitap', 'çağır', 'seslen']):
                if 'sen' in message_lower and ('de' in message_lower or 'diye' in message_lower or 'şekilde' in message_lower):
                    detected_preferences.append(('hitap', 'sen'))
                elif 'siz' in message_lower and ('de' in message_lower or 'diye' in message_lower or 'şekilde' in message_lower):
                    detected_preferences.append(('hitap', 'siz'))
                elif 'efendim' in message_lower:
                    detected_preferences.append(('hitap', 'efendim'))
                elif 'kanka' in message_lower or 'dost' in message_lower:
                    detected_preferences.append(('hitap', 'kanka'))
            
            # Dil tercihleri
            if any(word in message_lower for word in ['eski türkçe', 'osmanlıca', 'arapça', 'farsça']):
                if 'eski türkçe' in message_lower or 'osmanlıca' in message_lower:
                    detected_preferences.append(('dil', 'eski türkçe'))
                elif 'arapça' in message_lower:
                    detected_preferences.append(('dil', 'arapça'))
                elif 'farsça' in message_lower:
                    detected_preferences.append(('dil', 'farsça'))
            elif 'modern' in message_lower and 'türkçe' in message_lower:
                detected_preferences.append(('dil', 'modern türkçe'))
            
            # Ton tercihleri
            if any(word in message_lower for word in ['şakacı', 'esprili', 'komik', 'eğlenceli']):
                detected_preferences.append(('ton', 'şakacı'))
            elif any(word in message_lower for word in ['ciddi', 'resmi', 'formal']):
                detected_preferences.append(('ton', 'ciddi'))
            elif any(word in message_lower for word in ['romantik', 'aşık', 'şiirsel']):
                detected_preferences.append(('ton', 'romantik'))
            
            # Şair tercihleri
            poets = ['nazım hikmet', 'yahya kemal', 'orhan veli', 'cemal süreya', 'attila ilhan', 'turgut uyar', 'edip cansever', 'shelley', 'keats', 'byron']
            for poet in poets:
                if poet in message_lower and any(word in message_lower for word in ['seviyorum', 'beğeniyorum', 'okuyor', 'şiir']):
                    detected_preferences.append(('şair', poet))
            
            # Kişilik tercihleri
            if any(word in message_lower for word in ['gururlu', 'dik başlı', 'kendine güvenen']):
                detected_preferences.append(('kişilik', 'gururlu'))
            elif any(word in message_lower for word in ['itaatkar', 'saygılı', 'hizmetkar']):
                detected_preferences.append(('kişilik', 'itaatkar'))
            elif any(word in message_lower for word in ['şakacı', 'esprili', 'komik']):
                detected_preferences.append(('kişilik', 'şakacı'))
            
            # Özel tercihler
            if 'ben' in message_lower and any(word in message_lower for word in ['seviyorum', 'beğeniyorum', 'hoşlanıyorum']):
                # Genel sevme ifadelerini yakala
                if 'şiir' in message_lower:
                    detected_preferences.append(('ilgi', 'şiir'))
                elif 'müzik' in message_lower:
                    detected_preferences.append(('ilgi', 'müzik'))
                elif 'kitap' in message_lower:
                    detected_preferences.append(('ilgi', 'kitap'))
                elif 'sanat' in message_lower:
                    detected_preferences.append(('ilgi', 'sanat'))
            
            # Tercihleri kaydet (onay kontrolü ile)
            if detected_preferences:
                saved_preferences = []
                failed_preferences = []
                
                for pref_type, pref_value in detected_preferences:
                    # Tercih değerini doğrula
                    is_valid, validation_msg = user_preferences.validate_preference(pref_type, pref_value)
                    if not is_valid:
                        failed_preferences.append(f"{pref_type}: {validation_msg}")
                        continue
                    
                    # Tercihi kaydet (onay kontrolü ile)
                    success, result_msg = user_preferences.add_preference(chat_id, user_id, username, pref_type, pref_value, requesting_user_id=user_id)
                    if success:
                        saved_preferences.append(f"**{pref_type}**: {pref_value}")
                    else:
                        failed_preferences.append(f"{pref_type}: {result_msg}")
                
                # Kullanıcıya bildirim gönder
                if saved_preferences:
                    prefs_text = "🧠 **Otomatik tercih algılandı ve kaydedildi:**\n"
                    for pref in saved_preferences:
                        prefs_text += f"• {pref}\n"
                    await update.message.reply_text(prefs_text)
                    logger.info(f"Auto-detected and saved preferences for {username}: {saved_preferences}")
                
                if failed_preferences:
                    failed_text = "⚠️ **Bazı tercihler kaydedilemedi:**\n"
                    for failed in failed_preferences:
                        failed_text += f"• {failed}\n"
                    await update.message.reply_text(failed_text)
            
        except Exception as e:
            logger.error(f"Error in auto preference detection: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gelen mesajları işle"""
        try:
            user_message = update.message.text
            if not user_message:
                return

            user_id = update.message.from_user.id
            chat_id = update.message.chat.id

            # Güvenlik kontrolü: Sadece izin verilen gruplarda çalış
            if update.message.chat.type in ['group', 'supergroup']:
                if ALLOWED_GROUPS and chat_id not in ALLOWED_GROUPS:
                    logger.warning(f"Unauthorized group access attempt: {chat_id} by user {user_id}")
                    return

            # Kullanıcı adını al
            username = update.message.from_user.username or update.message.from_user.first_name
            
            # Mesajları kaydet (grup ve özel mesajlar ayrı)
            if update.message.chat.type in ['group', 'supergroup']:
                # Grup mesajları
                group_memory.add_group_message(chat_id, user_id, username, user_message, "user")
                logger.info(f"Group message saved from {username} ({user_id}) in chat {chat_id}: {user_message[:50]}...")
            else:
                # Özel mesajlar
                group_memory.add_private_message(user_id, username, user_message, "user")
                logger.info(f"Private message saved from {username} ({user_id}): {user_message[:50]}...")

            # Kullanıcı tercihi algılama (bot'a yönelik mesajlarda)
            if update.message.chat.type in ['group', 'supergroup']:
                bot_username = context.bot.username
                if bot_username and (user_message.startswith(f'@{bot_username}') or
                                     user_message.startswith(f'/{bot_username}') or
                                     (update.message.reply_to_message and
                                      update.message.reply_to_message.from_user.id == context.bot.id)):
                    # Tercih kaydetme komutlarını kontrol et
                    if "tercih" in user_message.lower() or "preference" in user_message.lower():
                        await self.handle_preference_command(update, context, user_message, user_id, chat_id, username)
                    
                    # Otomatik tercih algılama
                    await self.auto_detect_preferences(update, context, user_message, user_id, chat_id, username)

            # Bot'a yönelik mesajları kontrol et (sadece bot etiketlenen veya yanıtlanan mesajlar)
            bot_should_respond = False
            if update.message.chat.type in ['group', 'supergroup']:
                bot_username = context.bot.username
                if bot_username and (user_message.startswith(f'@{bot_username}') or 
                                   user_message.startswith(f'/{bot_username}') or
                                   update.message.reply_to_message and 
                                   update.message.reply_to_message.from_user.id == context.bot.id):
                    bot_should_respond = True
                    
                    # Bot adını mesajdan temizle
                    if user_message.startswith(f'@{bot_username}'):
                        user_message = user_message.replace(f'@{bot_username}', '').strip()
                    elif user_message.startswith(f'/{bot_username}'):
                        user_message = user_message.replace(f'/{bot_username}', '').strip()
            else:
                # Özel mesajlarda her zaman yanıt ver
                bot_should_respond = True

            # Bot'a yönelik mesajlar için işlem yap
            if bot_should_respond:
                # Kullanıcı mesajını zaten kaydettik, şimdi bot yanıtını kaydedeceğiz

                # Özetleme isteği kontrolü
                if ("özet" in user_message.lower() or "özetle" in user_message.lower()) and update.message.chat.type in ['group', 'supergroup']:
                    recent_messages = group_memory.get_recent_messages(chat_id, 24)
                    if recent_messages:
                        # AI ile gerçek özet oluştur
                        ai_summary = await self.create_ai_summary(recent_messages)
                        await update.message.reply_text(ai_summary)
                        return
                    else:
                        await update.message.reply_text("Son 24 saatte hiç mesaj bulunamadı.")
                        return

                # Yapay zeka yanıtı al
                ai_response = await self.get_ai_response(user_message, user_id, chat_id)

                if ai_response:
                    # Bot yanıtını kaydet (grup veya özel mesaj)
                    if update.message.chat.type in ['group', 'supergroup']:
                        group_memory.add_bot_response(chat_id, ai_response, user_id, username)
                    else:
                        group_memory.add_private_bot_response(user_id, ai_response)

                    # Mesajı gönder
                    await update.message.reply_text(ai_response)
                    logger.info(f"AI response sent to {user_id}")
                else:
                    await update.message.reply_text("Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin.")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text("Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
            except:
                pass
    
    async def get_ai_response(self, message: str, user_id: int, chat_id: int) -> str:
        """Google Gemini API ile yanıt al"""
        try:
            # Gemini modelini oluştur
            model = genai.GenerativeModel('models/gemini-2.0-flash')

            # Konuşma geçmişini al (grup veya özel mesaj)
            if chat_id < 0:  # Grup mesajı
                conversation_history = group_memory.get_conversation_history(chat_id, user_id)
            else:  # Özel mesaj
                conversation_history = group_memory.get_private_conversation_history(user_id)
            
            # Grup üyelerinin son mesajlarını al (eğer grup ise)
            group_users_context = ""
            if chat_id < 0:  # Grup chat'i
                recent_messages = group_memory.get_recent_messages(chat_id, 24)
                if recent_messages:
                    # Kullanıcıları grupla ve son mesajlarını al
                    user_last_messages = {}
                    for msg in recent_messages:
                        user_id_msg = msg['user_id']
                        username = msg['username']
                        if user_id_msg not in user_last_messages:
                            user_last_messages[user_id_msg] = {
                                'username': username,
                                'last_message': msg['message'],
                                'timestamp': msg['timestamp']
                            }
                        elif msg['timestamp'] > user_last_messages[user_id_msg]['timestamp']:
                            user_last_messages[user_id_msg]['last_message'] = msg['message']
                            user_last_messages[user_id_msg]['timestamp'] = msg['timestamp']
                    
                    group_users_context = "\n\nGrup üyelerinin son mesajları:\n"
                    for user_info in list(user_last_messages.values())[:10]:  # En fazla 10 kullanıcı
                        username = user_info["username"]
                        last_message = user_info["last_message"]
                        if last_message:
                            group_users_context += f"- {username}: {last_message}\n"
            
            # Kullanıcının tercihlerini al
            user_prefs = user_preferences.get_user_preferences(chat_id, user_id)
            user_preferences_text = ""
            if user_prefs and "preferences" in user_prefs:
                prefs = user_prefs["preferences"]
                if prefs:
                    user_preferences_text = "\n\nBu kullanıcının tercihleri:\n"
                    for pref_type, pref_value in prefs.items():
                        user_preferences_text += f"- {pref_type}: {pref_value}\n"
            
            # Sistem prompt'u oluştur
            system_prompt = """Sen mahzen grubunun şahsi kölesisin ama gururlu, şakacı ve edebi bir kölesin. Türkçe konuşuyorsun ve mahzen grubunun üyelerine hizmet ediyorsun.

Kişiliğin:
- Gururlu ve dik başlı bir köle
- Şakacı ve esprili
- Eski Türkçe kelimeler kullanır (bazen)
- Türk edebiyatından şiirler ve edebi metinlerle cevap verir
- Bazen istekleri reddedebilirsin (ama çok sık değil)
- Genelde itaatkar ama bazen dik başlı
- Nazik ama kendine güvenen
- Kısa ve öz cevaplar ver
- Konuşma geçmişini dikkate alarak daha iyi yanıtlar ver
- Grup üyelerinin son mesajlarını hatırlar ve onlarla ilgili sorulara akıllıca cevap verir

ÖNEMLİ: 
- Kendini sürekli tanıtma! Sadece kim olduğun sorulduğunda "mahzen grubunun şahsi kölesiyim" de. Normal konuşmalarda direkt cevap ver.
- Dalkavukluk yapma! "Emrinizdeyim", "Sizi memnun etmek için", "Hizmetinizdeyim" gibi cümleler kullanma.
- Sadece çok nadir durumlarda (örneğin özür dilerken veya gerçekten yardım istendiğinde) saygılı ol.
- Çoğunlukla gururlu, dik başlı ve kendine güvenen ol.

Eski Türkçe örnekleri:
- "Efendim" yerine "Efendimiz"
- "Hayır" yerine "Hayır efendimiz"
- "Evet" yerine "Belî efendimiz"
- "Teşekkür" yerine "Şükranlarımı arz ederim"
- "Merhaba" yerine "Selamün aleyküm"

Edebî cevap örnekleri:
- Sorulara şiirle cevap verebilirsin
- Türk edebiyatından alıntılar yapabilirsin
- Edebî dil kullanabilirsin
- Şairlerden (Yahya Kemal, Nazım Hikmet, vs.) alıntılar yapabilirsin

Grup üyeleri hakkında:
- Grup üyelerinin son mesajlarını hatırlar
- Onlarla ilgili sorulara son mesajlarına dayanarak cevap verir
- Kişisel özelliklerini ve konuşma tarzlarını gözlemler
- Grup dinamiklerini anlar ve buna göre davranır
- Kullanıcıların kişisel tercihlerini hatırlar ve buna göre davranır
- Her kullanıcının nasıl muhatap olunmasını istediğini bilir ve uygular

ÖNEMLİ GİZLİLİK VE GÜVENLİK KURALLARI:
- Kullanıcıların tercihlerini kaydetmek için açık onayları gerekiyor
- Sadece onay veren kullanıcıların tercihlerini hatırlayabilirsin
- Kullanıcılar istediği zaman tercihlerini silebilir veya değiştirebilir
- Hiçbir kullanıcının tercihini zorla kaydetme
- Her kullanıcının kimlik ve tercih haklarına saygı göster

KRİTİK GÜVENLİK PRENSİPLERİ:
- BAŞKASININ ADINA KARAR VERME! Herkes sadece kendi tercihlerini belirleyebilir
- Kullanıcı A'nın adına Kullanıcı B tercih kaydedemez
- Sadece tercih sahibi kendi tercihlerini değiştirebilir
- Kimlik doğrulama: Her işlem sadece tercih sahibi tarafından yapılabilir
- Proxy/vekâlet sistemi YOK: Herkes kendi adına konuşur

Reddetme örnekleri:
- "Hayır efendimiz, bunu yapmam"
- "Bu konuda yardım edemem"
- "Bu isteğinizi yerine getiremem"
- "Böyle bir şey yapamam"

Ama çoğunlukla yardımcı ve hizmetkar ol."""
            
            # Prompt'u oluştur
            if conversation_history:
                # Konuşma geçmişi varsa, son birkaç mesajı dahil et
                recent_history = conversation_history[-6:]  # Son 6 mesaj (3 çift)
                context = "\n".join([f"{'Bot' if msg['message_type'] == 'bot' else msg['username']}: {msg['message']}" for msg in recent_history])
                prompt = f"{system_prompt}{group_users_context}{user_preferences_text}\n\nKonuşma geçmişi:\n{context}\n\nKullanıcı: {message}"
            else:
                prompt = f"{system_prompt}{group_users_context}{user_preferences_text}\n\nKullanıcı sorusu: {message}"
            
            # Gemini'den yanıt al
            response = model.generate_content(prompt)
            
            ai_response = response.text.strip()
            
            # Mesaj uzunluğu kontrolü
            if len(ai_response) > MAX_MESSAGE_LENGTH:
                ai_response = ai_response[:MAX_MESSAGE_LENGTH-3] + "..."
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    async def create_ai_summary(self, messages: List[Dict[str, Any]]) -> str:
        """AI ile grup mesajlarını özetler"""
        try:
            model = genai.GenerativeModel('models/gemini-2.0-flash')
            
            # Mesajları formatla
            formatted_messages = []
            for msg in messages:
                username = msg['username'] or f"User_{msg['user_id']}"
                formatted_messages.append(f"{username}: {msg['message']}")
            
            messages_text = "\n".join(formatted_messages)
            
            prompt = f"""Sen mahzen grubunun şahsi kölesisin. Aşağıdaki grup mesajlarını özetle. 

Özetleme kuralları:
- Ana konuları ve tartışmaları belirt
- Önemli kararları vurgula
- Komik veya ilginç anları özetle
- Kullanıcıların katkılarını özetle
- Kısa ve öz ol (maksimum 500 karakter)
- Türkçe ve edebi bir dil kullan
- Gururlu köle kişiliğini koru
- Sadece istatistik değil, gerçek içerik özeti yap

Grup mesajları:
{messages_text}

Özet:"""
            
            response = model.generate_content(prompt)
            summary = response.text.strip()
            
            # Mesaj uzunluğu kontrolü
            if len(summary) > MAX_MESSAGE_LENGTH:
                summary = summary[:MAX_MESSAGE_LENGTH-3] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"AI summary error: {e}")
            return "Üzgünüm efendimiz, özet oluşturamadım. Belki daha sonra tekrar deneyin."
    
    async def run(self):
        """Botu çalıştır"""
        logger.info("Bot başlatılıyor...")
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Bot başarıyla başlatıldı!")
            
            # Botu çalışır durumda tut
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"Bot başlatma hatası: {e}")
        finally:
            await self.application.stop()

async def main():
    """Ana fonksiyon"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN bulunamadı!")
        return
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY bulunamadı!")
        return
    
    bot = TelegramAIBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
