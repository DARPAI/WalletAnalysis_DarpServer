from typing import Dict

from construct import Flag
from construct import Int64ul
from construct import Struct


def token_data_from_bonding_curve_token_acc_buffer(
    buffer: bytes,
) -> Dict[str, int | bool]:
    structure = Struct(
        "discriminator" / Int64ul,  # u64 (unsigned little-endian)
        "virtualTokenReserves" / Int64ul,  # u64 (unsigned little-endian)
        "virtualSolReserves" / Int64ul,  # u64 (unsigned little-endian)
        "realTokenReserves" / Int64ul,  # u64 (unsigned little-endian)
        "realSolReserves" / Int64ul,  # u64 (unsigned little-endian)
        "tokenTotalSupply" / Int64ul,  # u64 (unsigned little-endian)
        "complete" / Flag,  # bool
    )

    value = structure.parse(buffer)

    return dict(value)
