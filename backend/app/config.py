from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    trip_secret: str
    # 開発中にCloudflareクイックトンネルを使う場合、フロントエンドの
    # トンネルURLをここに設定する(例: https://xxxx.trycloudflare.com)。
    # trycloudflare.com全体を許可すると、他人の無関係なトンネルからも
    # アクセスできてしまうため、必ず自分のURLだけをピンポイントで許可する。
    cors_extra_origin: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
