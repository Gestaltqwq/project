"""
本项目需要的配置：
1. 数据库地址：连接到数据库的地址，例如 SQLite 数据库的路径。
2. JWT 认证配置：用于生成和验证 JWT 令牌的密钥、算法和过期时间。
3. 其他配置：根据项目需求添加其他配置项，如日志级别、缓存配置等。
"""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# .env 固定定位到项目根（work/），与运行目录无关，任意目录启动都能读到
_ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".env")


class Settings(BaseSettings):
    """
    应用配置类，包含数据库地址、JWT 认证配置等。
    """
    model_config = SettingsConfigDict(env_file=_ENV_PATH, env_file_encoding="utf-8", extra="ignore")

    #属性名都需要大写，并且与.env中的变量名一致，每个属性名都需要加上类型校验
    APP_NAME: str = "保险精准营销系统"
    DATABASE_URL: str = "sqlite:///./instance/starter.db"

    # JWT 认证（增强：密钥无默认值，必须从 .env 读取，且禁止占位符）
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256" # 算法：HS256，对称加密算法--验和签都是用一个密钥
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 默认 1 天

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _secret_must_be_strong(cls, v: str) -> str:
        """强制要求强随机密钥：拒绝空值和已知占位符"""
        placeholders = {
            "", "jwt-secret-change-me", "change-me",
            "change-me-to-random-string",
            "my-super-secret-key-change-in-production",
        }
        if v in placeholders or len(v) < 16:
            raise ValueError("JWT_SECRET_KEY 必须为 ≥16 位的强随机密钥，禁止使用占位符")
        return v

    # 大模型配置（openai 兼容接口：qwen/deepseek/glm/kimi）
    LLM_API_KEY: str = ""            # 生产环境强制从 .env 读取
    LLM_API_BASE: str = "https://api.deepseek.com/v1"  # 文档规范命名
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: int = 60            # 秒

    # 业务阈值
    HIGH_VALUE_PERCENTILE: float = 0.9   # 高潜客户分位数（默认 top 10%）



#模块级实例化：import 本模块时立即构造一个全局单例
settings = Settings()
   
