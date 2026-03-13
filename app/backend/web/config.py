import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from app.backend.web.app import Application
    

@dataclass
class SessionConfig:
    key: str
    

@dataclass
class AdminConfig:
    tg_id: str
    

@dataclass
class BotConfig:
    token: str
    admin: AdminConfig
    

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "bot_user"
    password: str = "bot_password"
    name: str = "bot_database"
    
    
@dataclass
class Config:
    session: SessionConfig
    bot: BotConfig
    database: DatabaseConfig
    admin: AdminConfig
    

def setup_config(app: "Application", config_path: str):
    import yaml
    
    with open(config_path, "r") as config_file:
        config_dict = yaml.safe_load(config_file)

    app.config = Config(
        session=SessionConfig(**config_dict["session"]),
        bot=BotConfig(
            token=config_dict["bot"]["token"],
            admin=AdminConfig(tg_id=config_dict["admin"]["tg_id"]),
        ),
        database=DatabaseConfig(**config_dict["database"]),
        admin=AdminConfig(tg_id=config_dict["admin"]["tg_id"]),
    )