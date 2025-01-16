import asyncio
import time
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import aiohttp
from settings import settings
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from utils.bonding_curve import bonding_curve_data
from utils.tools import calculate_win_rate_from_profits
from utils.tools import fetch_transactions_until_threshold
from utils.tools import get_token_price_bounding_curve
from utils.tools import get_token_price_exchange
from utils.tools import get_transaction_history
from utils.tools import process_transaction

SOL_DECIMALS: int = settings.sol_decimals
TRANSACTION_NUMBER_LIMIT_ROBOT: int = 200
TIME_INTERVAL_THRESHOLD: int = 3
FAST_TRANSACTIONS_PERCNET: float = 0.5
ONE_WEEK: int = 7 * 24 * 60 * 60
TRANSACTION_STATUS: str = "finalized"


async def get_purchased_tokens(wallet_address: str) -> List[str]:
    time_threshold: float = time.time() - ONE_WEEK
    async with aiohttp.ClientSession() as session:
        all_transactions: List[Dict[str, Any]] = (
            await fetch_transactions_until_threshold(
                session, wallet_address, time_threshold
            )
        )
        recent_transactions: List[Dict[str, Any]] = [
            item
            for item in all_transactions
            if item.get("blockTime", 0) >= time_threshold
        ]
        tasks: List[asyncio.Task[Tuple[Optional[str], float]]] = [
            process_transaction(session, item, wallet_address, time_threshold)
            for item in recent_transactions
        ]
        results: List[Tuple[Optional[str], float]] = await asyncio.gather(*tasks)
        purchased_tokens: Set[str] = set(mint for mint, _ in results if mint)
        return list(purchased_tokens)


async def calculate_profit_per_token(
    wallet_address: str, token: str
) -> Dict[str, Union[str, float]]:
    time_threshold: float = time.time() - ONE_WEEK
    async with aiohttp.ClientSession() as session:
        all_transactions: List[Dict[str, Any]] = (
            await fetch_transactions_until_threshold(
                session, wallet_address, time_threshold
            )
        )
        recent_transactions: List[Dict[str, Any]] = [
            item
            for item in all_transactions
            if item.get("blockTime", 0) >= time_threshold
        ]
        tasks: List[asyncio.Task[Tuple[Optional[str], float]]] = [
            process_transaction(session, item, wallet_address, time_threshold)
            for item in recent_transactions
        ]
        results: List[Tuple[Optional[str], float]] = await asyncio.gather(*tasks)
        token_profit: float = sum(
            trade_sol for mint, trade_sol in results if mint == token
        ) / (10**SOL_DECIMALS)
        return {"token": token, "profit": token_profit}


async def calculate_profit_for_each_token(wallet_address: str) -> Dict[str, float]:
    time_threshold: float = time.time() - ONE_WEEK
    async with aiohttp.ClientSession() as session:
        all_transactions: List[Dict[str, Any]] = (
            await fetch_transactions_until_threshold(
                session, wallet_address, time_threshold
            )
        )
        recent_transactions: List[Dict[str, Any]] = [
            item
            for item in all_transactions
            if item.get("blockTime", 0) >= time_threshold
        ]
        tasks: List[asyncio.Task[Tuple[Optional[str], float]]] = [
            process_transaction(session, item, wallet_address, time_threshold)
            for item in recent_transactions
        ]
        results: List[Tuple[Optional[str], float]] = await asyncio.gather(*tasks)
        token_profits: Dict[str, float] = defaultdict(float)
        for mint, trade_sol in results:
            if mint:
                token_profits[mint] += trade_sol / (10**SOL_DECIMALS)
        return token_profits


async def calculate_win_rate(wallet_address: str) -> float:
    token_profits: Dict[str, float] = await calculate_profit_for_each_token(
        wallet_address
    )
    win_rate: float = calculate_win_rate_from_profits(token_profits)
    return win_rate


async def calculate_total_profit(wallet_address: str) -> Dict[str, Any]:
    token_profits: Dict[str, float] = await calculate_profit_for_each_token(
        wallet_address
    )
    win_rate: float = calculate_win_rate_from_profits(token_profits)
    total_profit: float = sum(token_profits.values())
    return {
        "total_profit": total_profit,
        "token_profits": token_profits,
        "win_rate": win_rate,
    }


async def is_bot_trading(wallet_address: str) -> Union[bool, str]:
    async with aiohttp.ClientSession() as session:
        recent_transactions: List[Dict[str, Any]] = await get_transaction_history(
            session,
            wallet_address,
            limit=TRANSACTION_NUMBER_LIMIT_ROBOT,
            commitment=TRANSACTION_STATUS,
        )
        if not recent_transactions:
            return f"Can not determine whether it is a bot, because the transaction history of {wallet_address} is empty."
        transaction_times: List[float] = [
            tx.get("blockTime", 0) for tx in recent_transactions if tx.get("blockTime")
        ]
        transaction_times.sort()
        intervals: List[float] = []
        for i in range(1, len(transaction_times)):
            intervals.append(transaction_times[i] - transaction_times[i - 1])
        fast_transactions: int = sum(
            1 for interval in intervals if interval < TIME_INTERVAL_THRESHOLD
        )
        if fast_transactions > len(intervals) * FAST_TRANSACTIONS_PERCNET:
            return True
        return False


async def get_token_price(token: str) -> Union[float, str]:
    async with AsyncClient(settings.solana_rpc) as client:
        _, token_data = await bonding_curve_data(client, Pubkey.from_string(token))

        if token_data is None:
            return f"Cannot get price of {token}, because the state of its bonding curve can not be determined."

        token_price: Optional[float]
        if token_data["complete"]:
            token_price = await get_token_price_exchange(str(token))
        else:
            token_price = await get_token_price_bounding_curve(token_data)

        if token_price is None:
            return f"Can not get price of {token}, pls retry later"

        return token_price
