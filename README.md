# CraftLab

Каталог мастер-классов по рукоделию. Публикуйте пошаговые инструкции с фотографиями, выбирайте техники, указывайте материалы и их количество. Подписывайтесь на мастеров, сохраняйте публикации в избранное и собирайте общий список материалов в PDF. Количества одинаковых материалов в нескольких мастер-классах суммируются.

Автор адаптации и доработок — Рябуха Олег.

Python 3.11, Django 4.2, Django REST Framework, React 17, PostgreSQL 13; для локального запуска доступна SQLite. API использует токены Djoser. Доступ к редактированию публикаций имеют автор и администратор.

## Локальный запуск в PowerShell

Из корня проекта:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Copy-Item backend\.env.example backend\.env
# Замените SECRET_KEY в backend\.env собственным случайным значением.
.venv\Scripts\python.exe backend\manage.py migrate
.venv\Scripts\python.exe backend\manage.py seed_demo
.venv\Scripts\python.exe backend\manage.py createsuperuser
.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

Во втором терминале:

```powershell
cd frontend
npm.cmd ci --legacy-peer-deps --no-audit --no-fund
npm.cmd start
```

Откройте [каталог](http://localhost:3000/recipes), [API](http://127.0.0.1:8000/api/) или [админку](http://127.0.0.1:8000/admin/). Требуется Node.js 22 или 24. Команды start/build включают режим совместимости OpenSSL для сохранённой сборки CRA 4. Для разработки React проксирует API и изображения на порт 8000.

SQLite хранится в `backend/db.sqlite3` по умолчанию; значение `DB_NAME` из `.env.example` также разрешается относительно каталога backend. Для PostgreSQL задайте `DB_ENGINE=django.db.backends.postgresql`, `DB_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST` и `DB_PORT`. Секреты и локальные БД исключены из Git.

`seed_demo` загружает 10 материалов, две техники и два мастер-класса с простыми иллюстрациями. Повторный запуск не дублирует записи. У демоавтора `craftlab_demo` нет пароля; для работы зарегистрируйте свой аккаунт через интерфейс. Отдельная загрузка справочника: `.venv\Scripts\python.exe backend\manage.py add_data backend\ingredients.csv`.

## Запуск в Docker с PostgreSQL

```powershell
Copy-Item infra\.env.example infra\.env
# Укажите собственные SECRET_KEY и POSTGRES_PASSWORD в infra\.env.
docker compose -f infra/docker-compose.yml up --build -d
docker compose -f infra/docker-compose.yml exec backend python manage.py seed_demo
docker compose -f infra/docker-compose.yml exec backend python manage.py createsuperuser
```

Откройте [CraftLab](http://localhost:8081/recipes). Образы приложения собираются из локальных исходников, миграции и collectstatic выполняются при запуске backend. Nginx получает сборку React из отдельного тома. Для остановки: `docker compose -f infra/docker-compose.yml down`. БД и изображения остаются в томах.

## API

Спецификация: `docs/openapi-schema.yml` (в Docker — `/api/docs/openapi-schema.yml`). Названия маршрутов и JSON-полей стабильны:

| Маршрут / поле | Смысл в CraftLab |
| --- | --- |
| `/api/recipes/` | Мастер-классы |
| `text`, `cooking_time` | Инструкция и время выполнения в минутах |
| `/api/ingredients/`, `ingredients` | Материалы и необходимые количества |
| `/api/tags/` | Техники рукоделия |
| `/api/recipes/{id}/shopping_cart/` | Добавление и удаление мастер-класса из списка материалов |
| `/api/recipes/download_shopping_cart/` | Сводный PDF с материалами текущего пользователя |
| `/api/recipes/{id}/favorite/` | Избранное |
| `/api/users/{id}/subscribe/`, `/api/users/subscriptions/` | Подписки и публикации мастеров |

Пример тела POST `/api/recipes/` с заголовком `Authorization: Token <ваш токен>` (ID материалов и техник берите из API; `image` содержит настоящее изображение PNG/JPEG в base64):

```json
{
  "name": "Подставка из хлопкового шнура",
  "text": "Отмерьте шнур. Уложите спиралью. Закрепите витки.",
  "cooking_time": 30,
  "tags": [1],
  "ingredients": [{"id": 10, "amount": 3}],
  "image": "data:image/png;base64,<изображение>"
}
```

Поиск материалов: `/api/ingredients/?name=Шнур`; фильтры каталога: `?tags=decor`, `?author=1`, `?is_favorited=1`, `?is_in_shopping_cart=1`. Списки избранного и материалов зависят от авторизованного пользователя.

## Проверки

```powershell
.venv\Scripts\python.exe backend\manage.py check
.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe backend\manage.py test recipes
cd frontend
npm.cmd test -- --watchAll=false --runInBand
npm.cmd run build
```

Результаты и ограничения проверки находятся в `REVIEW.md`. GitHub Actions выполняет только проверки; публикация Docker-образов, SSH-деплой и отправка Telegram-уведомлений отсутствуют.

## Лицензия

Лицензия MIT и обязательное уведомление сохранены в `LICENSE`. Шрифт DejaVu используется для кириллицы в PDF; его уведомления находятся в `backend/recipes/fonts/LICENSE.txt`.
