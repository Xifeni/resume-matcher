#!/bin/sh

# Генерируем config.js на лету, подставляя значение из переменной окружения Docker.
# Если переменная не передана, используем дефолтное значение (например, http://localhost:5000)
API_URL=${VITE_API_URL:-"http://localhost:5000"}

echo "window.__ENV__ = {" > /usr/share/nginx/html/config.js
echo "  VITE_API_URL: '${API_URL}'" >> /usr/share/nginx/html/config.js
echo "};" >> /usr/share/nginx/html/config.js

# Запускаем оригинальную команду (обычно это запуск nginx)
exec "$@"
