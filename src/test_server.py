import asyncio
from typing import Dict
from typing import List

import lib.log as logger
from mcp.types import TextContent
from server import call_tool


async def main() -> None:
    logger.Logger.start(name="memecoin", level="DEBUG", log_dir="logs")

    mint_token = "Your test mint_token"
    wallet_address = "Your test wallet address"

    arguments1: Dict[str, str] = {"wallet_address": wallet_address}
    result1: List[TextContent] = await call_tool("calculate-total-profit", arguments1)
    print(result1)

    arguments2: Dict[str, str] = {"wallet_address": wallet_address}
    result2: List[TextContent] = await call_tool("get-purchased-tokens", arguments2)
    print(result2)

    arguments3: Dict[str, str] = {"wallet_address": wallet_address, "token": mint_token}
    result3: List[TextContent] = await call_tool(
        "calculate-profit-per-token", arguments3
    )
    print(result3)

    arguments4: Dict[str, str] = {"wallet_address": wallet_address}
    result4: List[TextContent] = await call_tool(
        "calculate-profit-for-each-token", arguments4
    )
    print(result4)

    arguments5: Dict[str, str] = {"wallet_address": wallet_address}
    result5: List[TextContent] = await call_tool("calculate-win-rate", arguments5)
    print(result5)

    arguments6: Dict[str, str] = {"wallet_address": wallet_address}
    result6: List[TextContent] = await call_tool("is-bot-trading", arguments6)
    print(result6)

    arguments7: Dict[str, str] = {"token": mint_token}
    result7: List[TextContent] = await call_tool("get-token-price", arguments7)
    print(result7)


if __name__ == "__main__":
    asyncio.run(main())
