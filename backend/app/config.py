from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://overbudget:overbudget@db:3306/overbudget"
    redis_url: str = "redis://redis:6379/0"
    attachments_path: str = "/data/attachments"
    debug: bool = False

    app_username: str = "admin"
    app_password: str = "changeme"
    jwt_secret: str = "change-this-secret"
    gpg_passphrase: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
