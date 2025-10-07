# Telegram AI Bot

Bu proje Telegram gruplarında çalışan yapay zeka destekli bir bot içerir.

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyasını oluşturun ve gerekli API anahtarlarını ekleyin:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

3. Botu çalıştırın:
```bash
python main.py
```

## Özellikler

- Telegram gruplarında mesajları dinler
- Google Gemini yapay zekası ile sorulara cevap verir
- Grup yönetimi özellikleri
- Hata yönetimi ve loglama

## Konfigürasyon

Bot ayarları `config.py` dosyasından yapılabilir.
