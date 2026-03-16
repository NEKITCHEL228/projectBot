# 📈 BirzjaGameBot

> Telegram-бот для групповой игры на бирже — покупайте и продавайте акции, следите за рынком и побеждайте соперников!

## 👤 Автор

**Малютин Никита Михайлович**

[![Email](https://img.shields.io/badge/Email-maluitin4589%40mail.ru-red?style=flat&logo=mail.ru)](mailto:maluitin4589@mail.ru)
[![Telegram](https://img.shields.io/badge/Telegram-@Nikita791-2CA5E0?style=flat&logo=telegram)](https://t.me/Nikita791)

---

## 🎮 Об игре

**BirzjaGameBot** — многопользовательская игра для Telegram-групп. Каждый игрок начинает с одинаковым капиталом и торгует акциями четырёх компаний. После каждого раунда цены меняются случайным образом — рынок непредсказуем. Побеждает тот, кто к концу игры накопит наибольший капитал.

### Компании на бирже

| Тикер | Базовая цена |
|---|---|
| `TELEGRAM` | 50 ₽ |
| `VK` | 30 ₽ |
| `HAMSTERCOMBAT` | 15 ₽ |
| `BIGDATA` | 80 ₽ |

---

## 🛠 Технологии

- **Python 3.11+**
- **aiohttp** — асинхронный веб-сервер
- **SQLAlchemy 2.0** (async) + **asyncpg** — работа с БД
- **PostgreSQL** — хранилище данных
- **Alembic** — миграции
- **Pydantic v2** — валидация Telegram Updates
- **Marshmallow** — сериализация REST API
- **aiohttp-session** + **aiohttp-apispec** — сессии и Swagger

---

## 📁 Структура проекта

```
app/
└── backend/
    ├── admin/          # Модель, маршруты и вьюхи администратора
    ├── base/           # BaseAccessor с lifecycle-хуками
    ├── game/           # Модели игры, игроков, акций и балансов
    ├── user/           # Модель пользователя
    ├── store/
    │   ├── admin/      # Доступ к данным администратора
    │   ├── bot/        # BotRouter, BotManager, обработчики команд
    │   ├── database/   # Подключение к БД, SQLAlchemy base
    │   ├── game/       # Игровая логика, покупка/продажа акций
    │   ├── tg_api/     # Telegram API accessor, Poller, Pydantic-схемы
    │   └── user/       # Доступ к данным пользователя
    └── web/            # Application, Config, Middlewares, Routes
```

### Архитектурные слои

```
Telegram API
     ↓  long polling
TgApiAccessor → Poller
     ↓
BotManager (обработка Updates)
     ↓
BotRouter (роутинг по командам / callback / pending)
     ↓
command_handlers (бизнес-логика)
     ↓
GameAccessor / UserAccessor / AdminAccessor
     ↓
PostgreSQL (SQLAlchemy async)
```

---

## ⚙️ Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/BirzjaGameBot.git
cd BirzjaGameBot
```

### 2. Настройка конфигурации

Скопируйте пример конфига и заполните значения:

```bash
cp config.yml.example config.yml
```

```yaml
# config.yml
bot:
  token: "YOUR_TELEGRAM_BOT_TOKEN"

database:
  host: localhost
  port: 5432
  user: bot_user
  password: bot_password
  name: bot_database

admin:
  tg_id: "123456789"
  password: "your_admin_password"
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

### 4. Запуск локально

```bash
# Установка зависимостей (через uv)
uv sync

# Или через pip
pip install -r requirements.txt

# Применение миграций
alembic upgrade head

# Запуск
python main.py
```

---

## 🤖 Команды бота

### Главное меню

| Команда / Кнопка | Описание |
|---|---|
| `/start` | Открыть главное меню |
| `Начать игру` | Создать лобби в текущем чате |
| `Покинуть игру` | Покинуть лобби (до старта) |
| `Показать статистику` | Личная статистика |
| `Правила игры` | Описание правил |

### Игровое меню (во время игры)

| Команда / Кнопка | Описание |
|---|---|
| `Купить Акции` | Показать список акций с ценами |
| `Продать Акции` | Показать портфель с кнопками продажи |
| `Просмотреть портфель` | Текущий портфель и балансы |
| `⏭ Завершить Ход` | Завершить торги в этом раунде |
| `🏁 Завершить игру` | Досрочно завершить игру (с подтверждением) |
| `/buy ТИКЕР КОЛИЧЕСТВО` | Купить акции. Пример: `/buy TELEGRAM 5` |
| `/sell ТИКЕР КОЛИЧЕСТВО` | Продать акции. Пример: `/sell VK 3` |

---

## 🔄 Игровой процесс

```
Создание лобби
      ↓
Присоединение игроков (inline-кнопка)
      ↓
Старт игры → Раунд 1 (начальные цены)
      ↓
┌─────────────────────────────┐
│  Торги: покупка / продажа   │
│  Игроки завершают ход        │
│  Когда все завершили → ↓    │
└─────────────────────────────┘
      ↓
Изменение цен (случайные события)
Пересчёт балансов всех игроков
      ↓
Следующий раунд или Конец игры
      ↓
Итоговый рейтинг + обновление статистики
```

### Система событий

Каждый раунд цены меняются по вероятностной таблице:

| Изменение | Вероятность |
|---|---|
| ±3% | 25% |
| ±8% | 20% |
| ±15% | 15% |
| ±20% | 12% |
| ±30% | 10% |
| ±50% | 7% |
| ±99% | 5% |
| ±228% | 3% |
| ±777% | 2% |
| ±1000% | 1% |

---

## 🗄 Модели базы данных

```
app_user
  ├── user_id (PK)
  ├── tg_id (UNIQUE)
  ├── name
  ├── max_balance
  ├── games_played
  └── games_won

game
  ├── game_id (PK)
  ├── chat_id
  ├── game_status (waiting_for_players | in_progress | finished)
  ├── game_trading_session_round
  └── max_rounds

game_user (связь игра ↔ пользователь)
  ├── game_user_id (PK)
  ├── game_id (FK → game)
  └── user_id (FK → app_user)

user_balance (баланс игрока в игре)
  ├── user_balance_id (PK)
  ├── game_user_id (FK → game_user)
  ├── full_balance      (pure + shares)
  ├── pure_balance      (свободные деньги)
  └── company_share_balance

company_shares (акции компаний в игре)
  ├── company_share_id (PK)
  ├── game_id (FK → game)
  ├── company_share_name
  └── company_share_price

user_company_share (портфель игрока)
  ├── user_company_share_id (PK)
  ├── game_user_id (FK → game_user)
  ├── company_share_id (FK → company_shares)
  └── company_share_count
```

---

## 🎬 Демонстрация

[![Demo Video](https://img.shields.io/badge/Google%20Drive-Смотреть%20демо-4285F4?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/drive/folders/14sb7sYCsKiKaJpPBsgKvmHgrtFMd96lw?usp=sharing)

---

## 📊 Диаграмма базы данных

[![DB Diagram](https://img.shields.io/badge/dbdiagram.io-Открыть%20схему-blue?style=for-the-badge&logo=databricks)](https://dbdiagram.io/d/69adc89df18be96a591c056b)


---

## 🔐 REST API (Admin)

| Метод | Endpoint | Описание |
|---|---|---|
| `POST` | `/admin.login` | Авторизация администратора |
| `GET` | `/admin.current` | Текущий администратор |

Swagger UI доступен по адресу: `http://localhost:8080/docs`

---

## 🧪 Тесты

```bash
pytest
```

---

## 📝 Переменные окружения

Все настройки берутся из `config.yml`. Путь к файлу передаётся при запуске через `main.py`.

---

## 📌 Known Issues / TODO

- [ ] Состояние лобби и ходов хранится в памяти — при перезапуске теряется
- [ ] Применить Alembic миграции вместо `create_all` при старте
- [ ] Добавить rate limiting на торговые команды
- [ ] Записывать историю изменения цен акций в БД