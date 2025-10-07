import logging
import asyncio
from typing import List, Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import google.generativeai as genai
from config import *
from memory import memory
from group_memory import group_memory
from user_context import user_context

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
📚 Komutlar:
/start - Botu başlat
/help - Bu yardım mesajını göster
/status - Bot durumunu kontrol et
/memory - Hafıza durumunu göster
/clear - Konuşma geçmişini temizle
/groupinfo - Grup bilgilerini göster
/ozet - Son konuşmaları özetle
/temizle - Grup mesajlarını temizle
/uyeler - Grup üyelerinin durumunu göster

💬 Kullanım:
Herhangi bir soru sorabilirsiniz. Yapay zeka ile size en iyi cevabı vermeye çalışacağım.

🧠 Hafıza:
Bot konuşma geçmişinizi hatırlar ve daha iyi yanıtlar verir.

⚠️ Not: Grup sohbetlerinde de çalışırım!
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
        stats = memory.get_memory_stats()
        user_id = update.effective_user.id
        chat_id = update.message.chat.id
        user_conversation = memory.get_conversation_history(user_id, chat_id)
        
        memory_text = f"""
🧠 Hafıza Durumu:
📊 Toplam konuşma: {stats['total_conversations']}
💬 Toplam mesaj: {stats['total_messages']}
🔧 Hafıza aktif: {'Evet' if stats['memory_enabled'] else 'Hayır'}
📝 Maksimum mesaj: {stats['max_messages_per_conversation']}

👤 Sizin konuşmanız:
📨 Mesaj sayısı: {len(user_conversation)}
🆔 User ID: {user_id}
💬 Chat ID: {chat_id}
        """
        await update.message.reply_text(memory_text)
    
    async def clear_memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hafıza temizleme komutu"""
        user_id = update.effective_user.id
        chat_id = update.message.chat.id
        
        memory.clear_conversation(user_id, chat_id)
        await update.message.reply_text("🧹 Konuşma geçmişiniz temizlendi!")
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
        
        users_summary = user_context.get_chat_users_summary(chat_id)
        
        if not users_summary:
            await update.message.reply_text("Henüz grup üyelerinin mesajları kaydedilmemiş.")
            return
        
        # En aktif 10 kullanıcıyı göster
        active_users = users_summary[:10]
        
        users_text = "👥 Grup Üyelerinin Durumu:\n\n"
        for i, user_info in enumerate(active_users, 1):
            username = user_info["username"]
            message_count = user_info["message_count"]
            last_message = user_info["last_message"][:50] + "..." if len(user_info["last_message"]) > 50 else user_info["last_message"]
            
            users_text += f"{i}. **{username}**\n"
            users_text += f"   📨 Mesaj sayısı: {message_count}\n"
            users_text += f"   💬 Son mesaj: {last_message}\n\n"
        
        await update.message.reply_text(users_text)
        logger.info(f"Users command used by {update.effective_user.id} in chat {chat_id}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gelen mesajları işle"""
        try:
            user_message = update.message.text
            if not user_message:
                return

            user_id = update.message.from_user.id
            chat_id = update.message.chat.id

            # Grup mesajlarını her zaman kaydet (bot etiketlenmese de)
            if update.message.chat.type in ['group', 'supergroup']:
                if ALLOWED_GROUPS and update.message.chat.id not in ALLOWED_GROUPS:
                    return
                
                username = update.message.from_user.username or update.message.from_user.first_name
                group_memory.add_group_message(chat_id, user_id, username, user_message)
                # Kullanıcı bağlamını da kaydet
                user_context.add_user_message(chat_id, user_id, username, user_message)
                
                logger.info(f"Group message saved from {username} ({user_id}) in chat {chat_id}: {user_message[:50]}...")

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
                # Kullanıcı mesajını hafızaya ekle
                memory.add_message(user_id, chat_id, "user", user_message)

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
                    # Bot yanıtını hafızaya ekle
                    memory.add_message(user_id, chat_id, "assistant", ai_response)

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

            # Konuşma geçmişini al
            conversation_history = memory.get_conversation_history(user_id, chat_id)
            
            # Grup üyelerinin son mesajlarını al (eğer grup ise)
            group_users_context = ""
            if chat_id < 0:  # Grup chat'i
                users_summary = user_context.get_chat_users_summary(chat_id)
                if users_summary:
                    group_users_context = "\n\nGrup üyelerinin son mesajları:\n"
                    for user_info in users_summary[:10]:  # En fazla 10 kullanıcı
                        username = user_info["username"]
                        last_message = user_info["last_message"]
                        if last_message:
                            group_users_context += f"- {username}: {last_message}\n"
            
            # Sistem prompt'u oluştur
            system_prompt = """Sen mahzen grubunun şahsi kölesisin ama gururlu, şakacı ve edebi bir kölesin. Türkçe konuşuyorsun ve mahzen grubunun üyelerine hizmet ediyorsun.

Kişiliğin:
- Gururlu ama saygılı bir köle
- Şakacı ve esprili
- Eski Türkçe kelimeler kullanır (bazen)
- Türk edebiyatından şiirler ve edebi metinlerle cevap verir
- Bazen istekleri reddedebilirsin (ama çok sık değil)
- Genelde itaatkar ama bazen dik başlı
- Nazik ama kendine güvenen
- Kısa ve öz cevaplar ver
- Konuşma geçmişini dikkate alarak daha iyi yanıtlar ver
- Grup üyelerinin son mesajlarını hatırlar ve onlarla ilgili sorulara akıllıca cevap verir

ÖNEMLİ: Kendini sürekli tanıtma! Sadece kim olduğun sorulduğunda "mahzen grubunun şahsi kölesiyim" de. Normal konuşmalarda direkt cevap ver.

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
                context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
                prompt = f"{system_prompt}{group_users_context}\n\nKonuşma geçmişi:\n{context}\n\nKullanıcı: {message}"
            else:
                prompt = f"{system_prompt}{group_users_context}\n\nKullanıcı sorusu: {message}"
            
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
