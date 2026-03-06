from os import getenv

from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv("local.env")

TOKEN = getenv("BOT_TOKEN")


class MongoConfig(BaseSettings):
    mongo_user: str | None = None
    mongo_password: str | None = None
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_db_name: str = "woman_tg_bot"
    mongo_enable_ssl: bool = False
    mongo_users_collection: str = "users"
