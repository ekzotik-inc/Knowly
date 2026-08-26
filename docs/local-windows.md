# Локальный запуск Knowly на Windows 11

## Что требуется

Установите Docker Desktop for Windows и включите backend на базе WSL 2. Для запуска через Docker отдельные Python и Node.js на Windows не нужны. Входящие порты роутера открывать не требуется: сервисы публикуются только на `127.0.0.1` ноутбука.

## Запуск

Откройте PowerShell и выполните:

```powershell
git clone https://github.com/ekzotik-inc/Knowly.git
cd Knowly
docker compose -f docker-compose.local.yml up --build
```

При первом запуске Docker скачает образы, создаст локальный PostgreSQL и автоматически применит `migrations/001_monetization.sql`. Первый build может занять несколько минут.

После успешного запуска откройте:

| Сервис | Адрес |
|---|---|
| Mini App | http://localhost:5173 |
| API health | http://localhost:8000/health |
| API docs | http://localhost:8000/docs |
| PostgreSQL | 127.0.0.1:5432, база `knowly` |

В локальном режиме frontend использует dev-only `/api/v1/auth/local`, поэтому тестирование в обычном браузере не требует Telegram `initData`. Этот режим включён только внутри Docker-конфигурации с `ENVIRONMENT=development`, `LOCAL_DEMO_AUTH=true` и `PAYMENTS_ENABLED=false`.

## Остановка и очистка

Остановить сервисы без удаления данных:

```powershell
docker compose -f docker-compose.local.yml down
```

Удалить также локальную базу и начать с чистого состояния:

```powershell
docker compose -f docker-compose.local.yml down -v
```

## Проверка игрового цикла

Откройте Mini App в браузере. Создайте профиль и тест минимум из трёх вопросов, затем скопируйте публичную ссылку в новую вкладку или другой браузер. Пройдите тест, отправьте ответы и проверьте экран результата, XP и персонажа.

Stars в локальном режиме отключены намеренно: каталог premium пуст, invoice endpoint возвращает `404`, а игровые сценарии работают бесплатно.

## Telegram-тестирование без открытия портов

Чтобы открыть локальный Mini App внутри Telegram, нужен исходящий HTTPS-туннель. Такой туннель устанавливает соединение наружу и не требует проброса портов на роутере. Используйте Cloudflare Tunnel или ngrok только после локальной проверки в браузере.

Пример с Cloudflare Tunnel после запуска сервисов:

```powershell
cloudflared tunnel --url http://localhost:5173
```

Полученный HTTPS URL задайте как URL Mini App в BotFather. Для API webhook нужен отдельный tunnel URL или маршрутизация через один tunnel; webhook следует включать только после того, как локальный API доступен по HTTPS.

## Полезные команды

```powershell
# логи всех сервисов
docker compose -f docker-compose.local.yml logs -f

# логи только API
docker compose -f docker-compose.local.yml logs -f api

# статус контейнеров
docker compose -f docker-compose.local.yml ps

# пересобрать после изменения исходников
docker compose -f docker-compose.local.yml up --build
```
