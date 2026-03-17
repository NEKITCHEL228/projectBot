import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from app.backend.web.app import Application
    
    

@dataclass
class AdminConfig:
    tg_id: int
    password: str
    

@dataclass
class BotConfig:
    token: str
    

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "bot_user"
    password: str = "bot_password"
    name: str = "bot_database"
    
    
@dataclass
class SessionConfig:
    key: str
    
@dataclass
class Config:
    bot: BotConfig
    database: DatabaseConfig
    admin: AdminConfig
    session: SessionConfig
    

def setup_config(app: "Application", config_path: str):
    import yaml
    
    with open(config_path, "r") as config_file:
        config_dict = yaml.safe_load(config_file)

    app.config = Config(
        bot=BotConfig(
            token=config_dict["bot"]["token"],
        ),
        database=DatabaseConfig(**config_dict["database"]),
        admin=AdminConfig(tg_id=config_dict["admin"]["tg_id"], password=config_dict["admin"]["password"]),
        session=SessionConfig(key=config_dict["session"]["key"])
    )