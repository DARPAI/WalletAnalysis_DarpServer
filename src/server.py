import json
from typing import Any

import lib.log as logger
import uvicorn
from analyser import calculate_profit_for_each_token
from analyser import calculate_profit_per_token
from analyser import calculate_total_profit
from analyser import calculate_win_rate
from analyser import get_purchased_tokens
from analyser import get_token_price
from analyser import is_bot_trading
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent
from mcp.types import Tool
from models import CalculateProfitForEachTokenInput
from models import CalculateProfitPerTokenInput
from models import CalculateTotalProfitInput
from models import CalculateWinRateInput
from models import GetPurchasedTokensInput
from models import GetTokenPriceInput
from models import IsBotTradingInput
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.routing import Route

server = Server("analysis-api")
sse = SseServerTransport("/messages/")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculate-total-profit",
            description="Calculate total profit of the given wallet address for the last 7 days.",
            inputSchema=CalculateTotalProfitInput.model_json_schema(),
        ),
        Tool(
            name="get-purchased-tokens",
            description="Fetch the list of tokens purchased by the given wallet address in the last 7 days.",
            inputSchema=GetPurchasedTokensInput.model_json_schema(),
        ),
        Tool(
            name="calculate-profit-per-token",
            description="Calculate the profit for a specific token traded by the given wallet address in the last 7 days.",
            inputSchema=CalculateProfitPerTokenInput.model_json_schema(),
        ),
        Tool(
            name="calculate-profit-for-each-token",
            description="Calculate the profit for each token traded by the given wallet address in the last 7 days.",
            inputSchema=CalculateProfitForEachTokenInput.model_json_schema(),
        ),
        Tool(
            name="calculate-win-rate",
            description="Calculate the win rate of the given wallet address based on its trading activity in the last 7 days.",
            inputSchema=CalculateWinRateInput.model_json_schema(),
        ),
        Tool(
            name="is-bot-trading",
            description="Check if the given wallet address exhibits bot-like trading behavior based on recent transactions.",
            inputSchema=IsBotTradingInput.model_json_schema(),
        ),
        Tool(
            name="get-token-price",
            description="Get the current price of a specific token by its mint address. The price is calculated either from an exchange or based on the bonding curve data, depending on the token's state.",
            inputSchema=GetTokenPriceInput.model_json_schema(),
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> Any:
    if name == "calculate-total-profit":
        try:
            input_data = CalculateTotalProfitInput(**arguments)
            result = await calculate_total_profit(input_data.wallet_address)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in calculate-total-profit: {e}")

    elif name == "get-purchased-tokens":
        try:
            input_data = GetPurchasedTokensInput(**arguments)
            result = await get_purchased_tokens(input_data.wallet_address)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in get-purchased-tokens: {e}")

    elif name == "calculate-profit-per-token":
        try:
            input_data = CalculateProfitPerTokenInput(**arguments)
            result = await calculate_profit_per_token(
                input_data.wallet_address, input_data.token
            )
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in calculate-profit-per-token: {e}")

    elif name == "calculate-profit-for-each-token":
        try:
            input_data = CalculateProfitForEachTokenInput(**arguments)
            result = await calculate_profit_for_each_token(input_data.wallet_address)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in calculate-profit-for-each-token: {e}")

    elif name == "calculate-win-rate":
        try:
            input_data = CalculateWinRateInput(**arguments)
            result = await calculate_win_rate(input_data.wallet_address)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in calculate-win-rate: {e}")

    elif name == "is-bot-trading":
        try:
            input_data = IsBotTradingInput(**arguments)
            result = await is_bot_trading(input_data.wallet_address)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in is-bot-trading: {e}")

    elif name == "get-token-price":
        try:
            input_data = GetTokenPriceInput(**arguments)
            result = await get_token_price(input_data.token)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            raise ValueError(f"Error in get-token-price: {e}")

    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


routes = [
    Route("/sse", endpoint=handle_sse),
    Mount("/messages/", app=sse.handle_post_message),
]

starlette_app = Starlette(routes=routes, debug=True)


def start_server(host: str = "0.0.0.0", port: int = 3005):
    logger.Logger.start(name="memecoin", level="DEBUG", log_dir="logs")

    logger.info(f"Starting server on {host}:{port}")
    try:
        uvicorn.run(starlette_app, host=host, port=port)
    except Exception as e:
        logger.error(f"Server startup error: {str(e)}")
        raise


if __name__ == "__main__":
    start_server()
