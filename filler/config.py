from typing import Optional

from genesis.blockchain.adapter import NodeAdapter
from genesis.blockchain.parser import Parser
from genesis.blockchains import Blockchain
from pydantic import AnyUrl, BaseSettings, validator


class Settings(BaseSettings):
    environment: str = "dev"
    node_blockchain: Blockchain
    node_url: Optional[AnyUrl] = None
    node_token: Optional[str] = None
    adapter: Optional[NodeAdapter] = None
    parser: Optional[Parser] = None
    sentry_dsn: Optional[str] = None

    class Config:
        env_file = ".env"

    @validator("node_blockchain", pre=True)
    @classmethod
    def convert_node_blockchain(cls, value: str) -> Blockchain:
        return Blockchain.from_name(value)


CONFIG = Settings()
