import os

from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    APP_SETTINGS_NAME: str
    APP_SERVER_URL: str
    APP_SECRET_KEY: str
    APP_SECURITY_SALT: str

    DISCORD_BOT_TOKEN: str
    DISCORD_ADMIN_USER_ID: int


class DevConfig(BaseConfig):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_HOST_PORT: int
    DB_SSL_MODE: str = 'disable'

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (f'postgresql+psycopg://'
                f'{self.DB_USER}:{self.DB_PASSWORD}@'
                f'{self.DB_HOST}:{self.DB_HOST_PORT}/{self.DB_NAME}'
                f'?sslmode={self.DB_SSL_MODE}')


class ProdConfig(BaseConfig):
    DATABASE_URL: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL.replace(
            "postgres://", "postgresql+psycopg://", 1
        )


env = os.getenv('APP_SETTINGS_NAME')

if env == 'production':
    settings = ProdConfig()
else:
    settings = DevConfig()
