import sentry_sdk
from fire import Fire

from filler.block_hash_to_number_mapper import block_hash_to_number_mapper
from filler.config import CONFIG
from filler.txid_to_block_mapper import txid_to_block_mapper

if CONFIG.sentry_dsn:
    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
        dsn=CONFIG.sentry_dsn
        environment=CONFIG.environment,
        traces_sample_rate=0.001,
    )

if __name__ == "__main__":
    Fire(
        dict(
            txid_to_block_mapper=txid_to_block_mapper,
            block_hash_to_number_mapper=block_hash_to_number_mapper,
        )
    )
