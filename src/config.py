from os import getenv

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv("local.env")

TOKEN = getenv("BOT_TOKEN")
MINI_APP_URL = getenv("MINI_APP_URL", "https://your-mini-app-domain.com/profile")


class MongoConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="local.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="MONGO_",
        extra="ignore",
    )
    
    user: str | None = None
    password: str | None = None
    host: str = "localhost"
    port: int = 27017
    db_name: str = "kibersport_tg_bot"
    enable_ssl: bool = False
    users_collection: str = "users"
    
    @property
    def mongo_user(self) -> str | None:
        return self.user
    
    @property
    def mongo_password(self) -> str | None:
        return self.password
    
    @property
    def mongo_host(self) -> str:
        return self.host
    
    @property
    def mongo_port(self) -> int:
        return self.port
    
    @property
    def mongo_db_name(self) -> str:
        return self.db_name
    
    @property
    def mongo_enable_ssl(self) -> bool:
        return self.enable_ssl
    
    @property
    def mongo_users_collection(self) -> str:
        return self.users_collection
