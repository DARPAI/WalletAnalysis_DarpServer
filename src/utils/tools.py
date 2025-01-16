import asyncio
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import aiohttp
import lib.log as logger
from decorator import retry_error  # type: ignore
from settings import settings
from solders.pubkey import Pubkey

REQUEST_MAX_TIMEOUT: int = 10
MINT_SOL: Pubkey = settings.mint_sol
SOL_DECIMALS: int = settings.sol_decimals
TOKEN_DECIMALS: int = settings.token_decimals
SOLANA_RPC = settings.solana_rpc
TRANSACTION_NUMBER_LIMIT_HISTORY = 1000
PROCESS_TRANSACTION_SEMAPHORE = 100
semaphore = asyncio.Semaphore(PROCESS_TRANSACTION_SEMAPHORE)
TRANSACTION_STATUS = "finalized"
JUP_URL: str = "https://api.jup.ag/price/v2"


def find_index(
    value_list: List[str], *values: str
) -> Tuple[Tuple[str, Optional[int]], ...]:
    result: List[Tuple[str, Optional[int]]] = []
    for value in values:
        try:
            index: int = value_list.index(value)
            result.append((value, index))
        except ValueError:
            result.append((value, None))
    return tuple(result)


def check_indices_in_range(
    indices: Tuple[Tuple[str, Optional[int]], ...], valid_indices: List[int]
) -> Optional[str]:
    index1: Optional[int] = indices[0][1]
    index2: Optional[int] = indices[1][1]

    in_index1: bool = index1 in valid_indices if index1 is not None else False
    in_index2: bool = index2 in valid_indices if index2 is not None else False

    if in_index1 == in_index2:
        return None
    elif in_index1:
        return indices[0][0]
    elif in_index2:
        return indices[1][0]
    return None


@retry_error(max_retries=10, retry_delay=1)
async def send_rpc_request(
    session: aiohttp.ClientSession,
    method: str,
    params: Optional[List[Any]] = None,
    timeout: int = REQUEST_MAX_TIMEOUT,
) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
    }

    async with session.post(
        SOLANA_RPC, json=payload, headers=headers, timeout=timeout
    ) as response:
        if response.status != 200:
            error_text: str = await response.text()
            logger.warning(
                f"RPC request failed with status {response.status}: {error_text}"
            )
            raise ValueError(f"RPC request failed: {error_text}")

        content_type: Optional[str] = response.headers.get("Content-Type", "")
        if content_type and "application/json" not in content_type:
            error_text = await response.text()
            logger.warning(
                f"Unexpected content type: {content_type}, response: {error_text}"
            )
            raise ValueError(f"Unexpected content type: {content_type}")

        response_json: Dict[str, Any] = await response.json()
        if response_json is None:
            logger.warning(
                f"Received empty response for method: {method}, params: {params}"
            )
            raise ValueError(f"Empty response received for {method}")

        return response_json.get("result")


async def get_transaction_details(
    session: aiohttp.ClientSession, signature: str
) -> Optional[Dict[str, Any]]:
    transaction_details: Optional[Dict[str, Any]] = await send_rpc_request(
        session,
        "getTransaction",
        params=[
            str(signature),
            {"encoding": "json", "maxSupportedTransactionVersion": 0},
        ],
    )
    return transaction_details


async def get_transaction_history(
    session: aiohttp.ClientSession,
    wallet_address: str,
    limit: int = 100,
    commitment=TRANSACTION_STATUS,
    before: Optional[str] = None,
) -> Optional[List[Dict[str, Any]]]:
    params: List[Any] = [
        str(wallet_address),
        {
            "limit": limit,
            "commitment": commitment,
            "encoding": "json",
            "maxSupportedTransactionVersion": 0,
        },
    ]
    if before:
        params[1]["before"] = before

    result = await send_rpc_request(session, "getSignaturesForAddress", params)
    return result


def is_trade_mint(
    data: Dict[str, Any],
    dev_id: str,
) -> bool:
    meta: Dict[str, Any] = data["meta"]
    pre_token_balances: List[Dict[str, Any]] = meta.get("preTokenBalances", [])
    post_token_balances: List[Dict[str, Any]] = meta.get("postTokenBalances", [])

    pre_balances_by_account_index: Dict[int, Dict[str, Any]] = {
        balance["accountIndex"]: balance for balance in pre_token_balances
    }

    found_dev_owner: bool = False
    for post_balance in post_token_balances:
        account_index: int = post_balance["accountIndex"]
        pre_balance: Optional[Dict[str, Any]] = pre_balances_by_account_index.get(
            account_index
        )

        if pre_token_balances:
            if pre_balance and post_balance["owner"] == dev_id:
                found_dev_owner = True
                if (
                    int(post_balance["uiTokenAmount"]["amount"])
                    - int(pre_balance["uiTokenAmount"]["amount"])
                ) != 0:
                    return True
        else:
            if post_balance["owner"] == dev_id:
                found_dev_owner = True
                if int(post_balance["uiTokenAmount"]["amount"]) != 0:
                    return True

    if not found_dev_owner:
        for post_balance in post_token_balances:
            account_index = post_balance["accountIndex"]
            pre_balance = pre_balances_by_account_index.get(account_index)

            if pre_token_balances:
                if pre_balance and post_balance["mint"] != str(MINT_SOL):
                    if (
                        int(post_balance["uiTokenAmount"]["amount"])
                        - int(pre_balance["uiTokenAmount"]["amount"])
                    ) != 0:
                        return True
            else:
                if post_balance["mint"] != str(MINT_SOL):
                    if int(post_balance["uiTokenAmount"]["amount"]) != 0:
                        return True
    return False


def find_mint(
    post_token_balances: List[Dict[str, Any]], account_keys: List[str]
) -> Optional[str]:
    for item in post_token_balances:
        if item["mint"] != str(MINT_SOL):
            return item["mint"]
    for key in account_keys:
        if key.endswith("pump"):
            return key
    return None


@retry_error(max_retries=5, retry_delay=1)
async def fetch_price_from_api(
    session: aiohttp.ClientSession, url: str, params: Dict[str, str]
) -> Optional[float]:
    async with session.get(url, params=params) as response:
        if response.status == 200:
            data: Dict[str, Any] = await response.json()
            return data["data"].get(params["ids"], {}).get("price")
        return None


async def get_token_price_exchange(mint_address: str) -> Optional[float]:
    params: Dict[str, str] = {
        "ids": str(mint_address),
        "vsToken": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    }
    async with aiohttp.ClientSession() as session:
        price = await fetch_price_from_api(session, JUP_URL, params)
        if price is None:
            return None
        return price


async def get_token_price_bounding_curve(token_data: Dict[str, Any]) -> Optional[float]:
    virtualTokenReserves: int = token_data["virtualTokenReserves"]
    virtualSolReserves: int = token_data["virtualSolReserves"]

    current_price_in_sol: float = (virtualSolReserves * 10**TOKEN_DECIMALS) / float(
        10**SOL_DECIMALS * virtualTokenReserves
    )
    current_solana_price: Optional[float] = await get_token_price_exchange(
        str(MINT_SOL)
    )

    if current_solana_price is None:
        return None
    return current_price_in_sol * float(current_solana_price)


async def calculate_sol_amount(
    meta: Dict[str, Any], account_keys: List[str], dev_id: str
) -> int:
    pre_balances: List[int] = meta.get("preBalances", [])
    post_balances: List[int] = meta.get("postBalances", [])
    dev_index_list: Tuple[Tuple[str, Optional[int]], ...] = find_index(
        account_keys, dev_id
    )
    dev_index: Optional[int] = dev_index_list[0][1]
    if dev_index is not None:
        trade_sol_lamport: int = int(post_balances[dev_index]) - int(
            pre_balances[dev_index]
        )
        return trade_sol_lamport
    else:
        return 0


async def calculate_sol_amount_without_fee(
    meta: Dict[str, Any], account_keys: List[str], dev_id: str
) -> int:
    pre_balances: List[int] = meta.get("preBalances", [])
    post_balances: List[int] = meta.get("postBalances", [])
    fee: int = meta.get("fee", 0)
    dev_index_list: Tuple[Tuple[str, Optional[int]], ...] = find_index(
        account_keys, dev_id
    )
    dev_index: Optional[int] = dev_index_list[0][1]
    if dev_index is not None:
        trade_sol_lamport: int = (
            int(post_balances[dev_index]) - int(pre_balances[dev_index]) + int(fee)
        )
        return trade_sol_lamport
    else:
        return 0


async def process_transaction(
    session: aiohttp.ClientSession,
    item: Dict[str, Any],
    wallet_address: str,
    time_threshold: int,
) -> Tuple[Optional[str], int]:
    async with semaphore:
        signature = item["signature"]
        transaction_details = await get_transaction_details(session, signature)
        if transaction_details is None:
            return None, 0

        block_time = transaction_details.get("blockTime")
        if block_time and block_time >= time_threshold:
            is_trade = is_trade_mint(transaction_details, str(wallet_address))
            if is_trade:
                meta = transaction_details["meta"]
                post_token_balances: List[Dict[str, Any]] = meta.get(
                    "postTokenBalances", []
                )
                transaction: Dict[str, Any] = transaction_details["transaction"]
                account_keys: List[str] = transaction["message"]["accountKeys"]
                mint = find_mint(post_token_balances, account_keys)
                trade_sol = await calculate_sol_amount_without_fee(
                    meta, account_keys, str(wallet_address)
                )
                return mint, trade_sol
        return None, 0


async def fetch_transactions_until_threshold(
    session: aiohttp.ClientSession, wallet_address: str, time_threshold: int
) -> List[Dict[str, Any]]:
    all_transactions: List[Dict[str, Any]] = []
    before: Optional[str] = None
    while True:
        history = await get_transaction_history(
            session,
            wallet_address,
            limit=TRANSACTION_NUMBER_LIMIT_HISTORY,
            commitment=TRANSACTION_STATUS,
            before=before,
        )
        if not history:
            logger.error(f"Can not get trade history of {wallet_address}")
            break
        all_transactions.extend(history)
        earliest_transaction = history[-1]
        earliest_block_time = earliest_transaction.get("blockTime")
        if earliest_block_time and earliest_block_time < time_threshold:
            break
        before = earliest_transaction["signature"]
    return all_transactions


def calculate_win_rate_from_profits(token_profits: Dict[str, int]) -> float:
    wins = 0
    losses = 0
    for _, profit in token_profits.items():
        if profit > 0:
            wins += 1
        elif profit < 0:
            losses += 1

    total_trades = wins + losses
    if total_trades == 0:
        return 0.0
    win_rate = (wins / total_trades) * 100
    return win_rate
