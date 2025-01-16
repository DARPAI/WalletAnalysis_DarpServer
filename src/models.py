from pydantic import BaseModel
from pydantic import Field


class GetPurchasedTokensInput(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address")


class CalculateProfitPerTokenInput(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address")
    token: str = Field(..., description="Token mint address")


class CalculateProfitForEachTokenInput(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address")


class CalculateWinRateInput(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address")


class CalculateTotalProfitInput(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address")


class IsBotTradingInput(BaseModel):
    wallet_address: str = Field(..., description="Solana wallet address")


class GetTokenPriceInput(BaseModel):
    token: str = Field(..., description="Token mint address")
