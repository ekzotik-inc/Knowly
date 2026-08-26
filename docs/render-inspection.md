# Render inspection

По состоянию на 26 августа 2026 года в Render workspace `hm-server` отображались активные сервисы `corporate-good-deeds`, `hm-server` и PostgreSQL `test_bd`. `hm-server` имел статус Deployed и runtime Node в регионе Oregon. Репозиторий Knowly подключается через Render Blueprint из `ekzotik-inc/Knowly`, ветка `main`.

Новый Blueprint Knowly после удаления background worker содержит free PostgreSQL, один Web Service `knowly-api` и Static Site `knowly-mini-app`. Форма Render показывала estimated pricing `$7 / month` за один новый Web Service, поэтому автоматическое создание нового сервиса без подтверждения не выполнялось.
