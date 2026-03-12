# Правила написания кода — Python backend

## Импорты

- Стандартные библиотеки → сторонние → внутренние (разделять пустой строкой)
- Для предотвращения циклических импортов использовать `typing.TYPE_CHECKING`:
  ```python
  import typing
  if typing.TYPE_CHECKING:
      from app.backend.web.app import Application
  ```
- Тяжёлые или нечасто нужные модули импортировать внутри функции:
  ```python
  def setup_config(app, config_path):
      import yaml  # не на верхнем уровне
      ...
  ```

## Типизация

- Использовать `X | None` вместо `Optional[X]`
- Аннотировать поля классов явно, даже если они выставляются позже:
  ```python
  class Application(AiohttpApplication):
      config: Config | None = None
      store: Store | None = None
  ```
- Для forward-reference использовать строковые аннотации: `"Application"`

## Конфигурация

- Каждый логический блок конфига — отдельный `@dataclass`
- Вложенность отражает структуру YAML:
  ```python
  @dataclass
  class BotConfig:
      token: str
      admin: AdminConfig

  @dataclass
  class Config:
      session: SessionConfig
      bot: BotConfig
      database: DatabaseConfig
      admin: AdminConfig
  ```
- Значения по умолчанию ставить только там, где они имеют смысл (например, `DatabaseConfig`)
- Создание конфига — в функции `setup_config(app, config_path)`, не в конструкторе

## Инициализация приложения (setup_*)

- Каждая подсистема инициализируется отдельной функцией `setup_<subsystem>(app)`
- Порядок вызовов в `setup_app` фиксирован:
  1. `setup_logging`
  2. `setup_config`
  3. сессии (cookie/session middleware)
  4. `setup_routes`
  5. `setup_aiohttp_apispec`
  6. `setup_middlewares`
  7. `setup_store`
- `setup_app` всегда возвращает `app`

## Сервисные классы — паттерн BaseAccessor

- Все аксессоры (DB, TG API, bot manager, ...) наследуют `BaseAccessor`
- Конструктор регистрирует lifecycle-хуки через `app.on_startup` / `app.on_cleanup`:
  ```python
  class BaseAccessor:
      def __init__(self, app: "Application"):
          self.app = app
          self.logger = getLogger("accessor")
          app.on_startup.append(self.connect)
          app.on_cleanup.append(self.disconnect)
  ```
- `connect` и `disconnect` — async-методы с сигнатурой `async def connect(self, app: "Application")`
- Новые аксессоры создаются через `setup_store(app)`, а не вручную

## Обёртки aiohttp

- Не использовать `aiohttp.web.Application` / `Request` / `View` напрямую
- Использовать кастомные подклассы из `app.backend.web.app`:
  ```python
  from app.backend.web.app import Application, Request, View
  ```

## Точка входа

- `main.py` всегда под guard `if __name__ == "__main__":`
- Путь к конфигу строить через `os.path.realpath(__file__)`, не через относительные пути

## Именование

- Функции-инициализаторы: `setup_<subsystem>`
- Аксессоры: `<Domain>Accessor` (например, `AdminAccessor`, `GameAccessor`)
- Схемы marshmallow: `<Entity>Schema`
- Модели (dataclass / SQLAlchemy): `<Entity>` без суффикса
