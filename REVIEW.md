# CraftLab — проверка изменений

Автор адаптации и доработок — Рябуха Олег.

Проверено 17 ноября 2026 года. Рабочая копия: `C:\ProjectAdaptations\2026-11-17\CraftLab`. История Git сохранена.

## Обзор

Прочитаны README, MIT LICENSE, структура backend/frontend/infra/docs, зависимости, Django-модели/сериализаторы/права/фильтры, React-формы и API-клиент, OpenAPI, Docker и GitHub Actions. Контрольная точка кода: `42983c630bf2fdac9ea855a6d29539f2c06675b7`.

Архитектура: Django/DRF с Djoser TokenAuthentication, React 17, PostgreSQL, Nginx, FPDF. Публикации с изображениями, техники, материалы и количества, подписки, избранное, список материалов и PDF сохранены. Backend-тестов не было; единственный frontend-тест проверял отсутствующую ссылку `learn react` и не покрывал сценарии приложения.

Лицензия MIT и обязательное уведомление в LICENSE сохранены. Добавлены уведомления шрифта DejaVu, используемого для русскоязычного PDF.

## Изменения

- Пользовательский интерфейс, заголовки/метаданные, формы, API-описания, admin и названия моделей для администратора приведены к мастер-классам, техникам и материалам.
- Стабильные API-маршруты, имена моделей и JSON-поля `recipes`, `ingredients`, `cooking_time`, `shopping_cart` сохранены для согласованной работы React и backend. Предметный смысл этих полей описан в README и OpenAPI.
- Справочники заменены десятью материалами. Команда `seed_demo` создаёт две техники и два мастер-класса с изображениями; её повторный запуск не дублирует данные. Демоавтор имеет неиспользуемый пароль.
- Добавлены отсутствовавшие начальные миграции. Для локального запуска доступна SQLite; PostgreSQL остаётся конфигурацией Docker. `add_data` использует Django ORM и не подключается к PostgreSQL при импорте команды.
- Django/DRF и непосредственные backend-зависимости приведены к совместимым с Python 3.11 версиям. React 17 / CRA 4 сохранены; для современного Node исправлен PostCSS и включён OpenSSL legacy provider. Сохранён один актуальный npm lock-файл, дублирующий yarn.lock удалён.
- PDF суммирует одинаковые количества из разных мастер-классов: устранён `Sum(distinct=True)`, который превращал `3 + 3` в `3`. Длинные названия материалов переносятся; путь к шрифту не зависит от рабочего каталога.
- Приватные списки требуют авторизации, а фильтры приватных списков для гостя возвращают пустую выдачу. Неверные количества материалов возвращают 400. Валидация тегов выполняется до записи, изменения вложенных данных атомарны; PATCH текста сохраняет существующие материалы и техники.
- Compose собирает оба приложения из локальных исходников, запускает миграции/collectstatic, ожидает готовность PostgreSQL и сборки frontend. Удалены прежние DockerHub-образы, адреса серверов, бейдж и задания SSH/DockerHub/Telegram из CI. CI выполняет только проверки.
- Удалены шаблонные CRA-подсказки, закомментированные заготовки, очевидные комментарии и неиспользуемая конфигурация API URL. Секреты в `.env.example` — безопасные заглушки.

## Проверки и результат

Команды запускаются из корня проекта, кроме явно указанного frontend:

| Проверка | Результат |
| --- | --- |
| `.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt` | Успешно, Python 3.11 |
| `.venv\Scripts\python.exe -m pip check` | No broken requirements found |
| `.venv\Scripts\python.exe backend\manage.py check` | 0 замечаний |
| `.venv\Scripts\python.exe backend\manage.py migrate --noinput` | Все миграции применены к новой SQLite |
| `.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run` | No changes detected |
| `.venv\Scripts\python.exe backend\manage.py seed_demo` (повторно) | 2 мастер-класса, 10 материалов, 2 техники |
| `.venv\Scripts\python.exe backend\manage.py test recipes` | **12 tests passed** |
| В frontend: `npm.cmd install --legacy-peer-deps --no-audit --no-fund` | Зависимости установлены, lock-файл обновлён |
| В frontend: `npm.cmd test -- --watchAll=false --runInBand` | **3 tests passed**, 1 suite |
| В frontend: `npm.cmd run build` | Compiled successfully, Node.js 24.16 |
| `docker compose -f infra/docker-compose.yml config --quiet` с копией `.env.example` | Конфигурация валидна |
| OpenAPI YAML, разбор через js-yaml | 17 маршрутов; формат 3.0.2, основные маршруты найдены |
| `git diff --check` | Без ошибок |

Backend-тесты проверяют регистрацию и вход по токену, публикацию инструкции с материалами, права автора, PATCH и замену количеств/техник, отклонение неверных/дублирующихся материалов без частичных записей, неизвестные техники, избранное и подписки с запретом дублей, фильтрацию, поиск материалов, авторизацию приватных операций. PDF прочитан библиотекой pypdf: заголовок на русском и сумма `Шнур хлопковый - 6 м` подтверждены; запись другого пользователя в список не попала.

HTTP smoke: реально запущены Django на `127.0.0.1:8000` и React dev server на `127.0.0.1:3009`; получены HTTP 200 для `/recipes`, `/admin/login/`, `/api/recipes/`, `/api/tags/`, `/api/ingredients/` и демоизображения. API и изображение проверены через React proxy, публикации получены из SQLite. После проверки оба процесса остановлены.

## Ограничения

Docker Desktop daemon не запущен: `docker version` не смог подключиться к pipe `dockerDesktopLinuxEngine`. Сборка/запуск контейнеров, PostgreSQL и Nginx во время этой проверки не выполнялись; выполнена проверка Compose, отдельные приложения и миграции проверены локально на SQLite. Node.js 22 в CI/Docker указан, локально проверен Node.js 24.16.

Ручная визуальная проверка интерфейса в браузере не выполнялась. Проверены Jest-компоненты, production build и HTTP-связка React → API → БД. Сборка сообщает о старой базе caniuse-lite и deprecated fs.F_OK в сохранённом CRA 4; это не мешает успешному завершению. Действующие production-секреты и внешние сервисы этому проекту не требуются.

## Запуск и сообщение коммита

Полные команды первого запуска — в README. После установки:

```powershell
.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
# Во втором терминале:
cd frontend
npm.cmd start
```

Либо `docker compose -f infra/docker-compose.yml up --build -d` после подготовки `infra/.env`.

Предложение сообщения будущего коммита: `Adapt CraftLab workshops, materials and PDF lists; make local startup reproducible`.
