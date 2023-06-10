from logging import getLogger
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection

from filler.utils import (
    create_task_safely,
    mongo_init,
    mongo_insert_many,
    stream_new_blocks,
)

logger = getLogger(__name__)


async def get_last_processed_block_number(collection: AsyncIOMotorCollection) -> int:
    transaction_count = await collection.estimated_document_count()
    if transaction_count < 100:
        return 1
    transaction_cursor = collection.find().skip(transaction_count - 1)
    last_transaction = await transaction_cursor.next()
    last_processed_block_number = last_transaction["block_number"]
    logger.info("Last processed block: %d", last_processed_block_number)
    return last_processed_block_number - 100


async def process_block(
    collection: AsyncIOMotorCollection,
    session: AsyncIOMotorClientSession,
    raw_block: dict,
) -> None:
    block_number = raw_block["block_num"]
    items = [
        dict(_id=transaction_dict["trx"]["id"], block_number=block_number)
        for transaction_dict in raw_block["transactions"]
    ]

    await mongo_insert_many(collection, session, items)


async def txid_to_block_mapper(start_block_height: Optional[int] = None) -> None:
    collection, session = await mongo_init("txid_to_block_map")
    # TODO paralelize
    # TODO handle chain reorgs
    # TODO terminate sessions and connections

    if start_block_height is None:
        start_block_height = await get_last_processed_block_number(collection)

    async for raw_block in stream_new_blocks(
        start_block_height=start_block_height,
        sleep_interval_seconds=1,
        n_blocks_ahead=100,
        block_height_key="block_num",
    ):
        # TODO block_height_key should be getting from ENV or from parser! now its hardcoded for eos
        logger.info(f"Processing block {raw_block['block_num']:,}")
        create_task_safely(process_block(collection, session, raw_block))
