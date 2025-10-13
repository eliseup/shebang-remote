import os

from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_HOST_PORT: int
    DB_SSL_MODE: str = 'disable'

    APP_SETTINGS_NAME: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (f'postgresql+psycopg://'
                f'{self.DB_USER}:{self.DB_PASSWORD}@'
                f'{self.DB_HOST}:{self.DB_HOST_PORT}/{self.DB_NAME}'
                f'?sslmode={self.DB_SSL_MODE}')


class DevConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    DB_SSL_MODE: str = 'require'


env = os.getenv('APP_SETTINGS_NAME')

if env == 'production':
    settings = ProdConfig()
else:
    settings = DevConfig()
