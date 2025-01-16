from pathlib import Path
from typing import Type
from typing import Union

from pydantic import validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from solders.pubkey import Pubkey


class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    solana_rpc: str = "https://api.mainnet-beta.solana.com"
    sol_decimals: int = 9
    token_decimals: int = 6
    mint_sol: Pubkey = Pubkey.from_string("So11111111111111111111111111111111111111112")
    pumpfun_program_id: Pubkey = Pubkey.from_string(
        "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
    )

    log_dir: Path = Path("logs")

    @validator(
        "mint_sol",
        "pumpfun_program_id",
        pre=True,
    )
    def parse_pubkey(cls: Type["Settings"], value: Union[str, Pubkey]) -> Pubkey:
        if isinstance(value, Pubkey):
            return value
        try:
            return Pubkey.from_string(value)
        except ValueError:
            raise ValueError(f"Invalid Pubkey: {value}")


settings: Settings = Settings()
