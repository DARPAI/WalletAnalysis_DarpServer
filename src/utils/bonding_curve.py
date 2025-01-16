from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from decorator import retry_error  # type: ignore
from settings import settings
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from utils.data_handler import token_data_from_bonding_curve_token_acc_buffer

BONDING_CURVE_SEED: str = "bonding-curve"


def get_bonding_curve_pda(mint: Pubkey, program_id: Pubkey) -> Pubkey:
    seeds: list[bytes] = [BONDING_CURVE_SEED.encode("utf-8"), bytes(mint)]
    pda: Pubkey
    pda, _ = Pubkey.find_program_address(seeds, program_id)
    if pda is None:
        raise ValueError("Failed to get bonding curve")
    return pda


@retry_error(max_retries=5, retry_delay=2)
async def get_bonding_curve_token_account(
    client: AsyncClient,
    bonding_curve: Pubkey,
) -> Dict[str, Any]:
    account_info = await client.get_account_info(bonding_curve)
    if account_info is None or account_info.value is None:
        raise ValueError("Failed to get account info")
    return account_info.value


async def bonding_curve_data(
    client: AsyncClient, mint: Pubkey
) -> Tuple[Pubkey, Optional[Dict[str, Any]]]:
    program_id: Optional[Pubkey] = settings.pumpfun_program_id
    assert program_id, "Can't find program id, please set it."

    bonding_curve: Pubkey = get_bonding_curve_pda(mint, program_id)
    account_info: Optional[Dict[str, Any]] = await get_bonding_curve_token_account(
        client, bonding_curve
    )
    if account_info and account_info.data:  # type: ignore
        token_data: Dict[str, Any] = token_data_from_bonding_curve_token_acc_buffer(
            account_info.data  # type: ignore
        )
        return bonding_curve, token_data
    else:
        return bonding_curve, None
