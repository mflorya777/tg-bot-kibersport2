#!/usr/bin/env python3
"""
Скрипт для получения текущего ngrok URL и обновления конфигурации мини-приложений.
"""
import json
import os
import sys
import requests
from pathlib import Path


def get_ngrok_url():
    """
    Получает текущий ngrok URL через ngrok API.
    
    Returns:
        str: ngrok URL или None
    """
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
    except Exception as e:
        print(f"⚠️  Не удалось получить URL через ngrok API: {e}", file=sys.stderr)
    
    # Пытаемся прочитать из файла
    ngrok_url_file = Path(".ngrok_url")
    if ngrok_url_file.exists():
        return ngrok_url_file.read_text().strip()
    
    return None


def update_mini_apps(ngrok_url: str):
    """
    Обновляет URL API в мини-приложениях.
    
    Args:
        ngrok_url: ngrok URL для API
    """
    mini_app_dir = Path("mini-app")
    if not mini_app_dir.exists():
        print("❌ Директория mini-app не найдена")
        return False
    
    html_files = [
        "index.html",
        "referral.html",
        "referral_settings.html",
        "promotions.html",
    ]
    
    updated = False
    for html_file in html_files:
        file_path = mini_app_dir / html_file
        if not file_path.exists():
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Ищем meta-тег с api-base-url
            import re
            pattern = r'<meta\s+name="api-base-url"\s+content="[^"]*">'
            replacement = f'<meta name="api-base-url" content="{ngrok_url}">'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                file_path.write_text(content, encoding="utf-8")
                print(f"✅ Обновлен {html_file}")
                updated = True
            else:
                # Если meta-тег не найден, добавляем его
                head_pattern = r'(<head>.*?<meta\s+name="viewport"[^>]*>)'
                new_meta = f'\\1\n    <meta name="api-base-url" content="{ngrok_url}">'
                if re.search(head_pattern, content, re.DOTALL):
                    content = re.sub(head_pattern, new_meta, content, flags=re.DOTALL)
                    file_path.write_text(content, encoding="utf-8")
                    print(f"✅ Добавлен meta-тег в {html_file}")
                    updated = True
        except Exception as e:
            print(f"⚠️  Ошибка при обновлении {html_file}: {e}", file=sys.stderr)
    
    return updated


def main():
    """Основная функция."""
    ngrok_url = get_ngrok_url()
    
    if not ngrok_url:
        print("❌ ngrok не запущен или URL не найден")
        print("💡 Запустите ngrok: ./scripts/start_ngrok.sh")
        sys.exit(1)
    
    print(f"🌐 Найден ngrok URL: {ngrok_url}")
    print("🔄 Обновление мини-приложений...")
    
    if update_mini_apps(ngrok_url):
        print("✅ Мини-приложения обновлены!")
    else:
        print("⚠️  Не удалось обновить мини-приложения")
    
    print(f"\n💡 Используйте этот URL в мини-приложениях:")
    print(f"   {ngrok_url}")


if __name__ == "__main__":
    main()
