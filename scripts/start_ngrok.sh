#!/bin/bash
# Скрипт для запуска ngrok туннеля для API сервера

set -e

# Порт API сервера
API_PORT=${API_PORT:-8000}

# Проверяем, установлен ли ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok не установлен!"
    echo "Установите ngrok: https://ngrok.com/download"
    exit 1
fi

echo "🚀 Запуск ngrok туннеля для порта $API_PORT..."
echo "📝 URL будет сохранен в файл .ngrok_url"
echo ""
echo "⚠️  Для остановки нажмите Ctrl+C"
echo ""

# Запускаем ngrok в фоне и сохраняем URL
ngrok http $API_PORT > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Ждем, пока ngrok запустится
sleep 3

# Получаем URL из ngrok API
NGROK_URL=""
MAX_ATTEMPTS=10
ATTEMPT=0

while [ -z "$NGROK_URL" ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 1
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -oP 'https://[a-z0-9]+\.ngrok\.io' | head -1)
    ATTEMPT=$((ATTEMPT + 1))
done

if [ -z "$NGROK_URL" ]; then
    echo "❌ Не удалось получить ngrok URL"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

# Сохраняем URL в файл
echo "$NGROK_URL" > .ngrok_url
echo "$NGROK_PID" > .ngrok_pid

echo "✅ ngrok запущен!"
echo "🌐 Публичный URL: $NGROK_URL"
echo "📄 URL сохранен в файл .ngrok_url"
echo "🆔 PID процесса: $NGROK_PID"
echo ""
echo "💡 Используйте этот URL в мини-приложениях:"
echo "   <meta name=\"api-base-url\" content=\"$NGROK_URL\">"
echo ""

# Функция для очистки при выходе
cleanup() {
    echo ""
    echo "🛑 Остановка ngrok..."
    kill $NGROK_PID 2>/dev/null || true
    rm -f .ngrok_url .ngrok_pid
    echo "✅ ngrok остановлен"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Ждем завершения
wait $NGROK_PID
