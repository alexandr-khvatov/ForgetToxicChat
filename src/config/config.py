from dataclasses import dataclass

from environs import Env
from sqlalchemy import URL

env = Env()
env.read_env(".env-dev")


@dataclass
class DatabaseConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_port: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных

    driver: str = "asyncpg"
    database_system: str = "postgresql"

    def build_connection_str(self) -> str:
        return URL.create(
            drivername=f"{self.database_system}+{self.driver}",
            username=self.db_user,
            database=self.database,
            password=self.db_password,
            port=int(self.db_port),
            host=self.db_host,
        ).render_as_string(hide_password=False)


@dataclass
class RedisConfig:
    db: str
    host: str
    port: int
    passwd: int
    username: int
    state_ttl: int
    data_ttl: int


@dataclass
class TgBot:
    token: str
    admins: dict
    max_admins_count: int
    page_size_stop_word: int
    max_stop_word_count: int
    ban_period: int
    remove_joins: bool
    model_path: str
    path_tokenizer: str
    group_reports: int  # todo: удалить или
    toxicity_service_url: str
    webhook_domain: str
    webhook_path: str
    ssl: str
    app_host: str = "0.0.0.0"
    app_port: str = 9000


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


config = Config(
    tg_bot=TgBot(
        token=env('BOT_TOKEN'),
        admins={},
        max_admins_count=50,
        page_size_stop_word=10,
        max_stop_word_count=100,
        ban_period=29,
        remove_joins=True,
        group_reports=-807049020,
        model_path=env('MODEL_PATH'),
        path_tokenizer=env('PATH_TOKENIZER'),
        toxicity_service_url=env('TOXICITY_SERVICE_URL'),
        webhook_domain=env('WEBHOOK_DOMAIN'),
        webhook_path=env('WEBHOOK_PATH'),
        ssl=env('SSL_SERT')
    ),
    db=DatabaseConfig(
        database=env('POSTGRES_DATABASE'),
        db_host=env('POSTGRES_HOST'),
        db_port=env('POSTGRES_PORT'),
        db_user=env('POSTGRES_USER'),
        db_password=env('POSTGRES_PASSWORD'),
    )
)
