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
    block_count = await collection.estimated_document_count()

    if block_count < 100:
        return 1

    block_cursor = collection.find().skip(block_count - 1)
    last_block = await block_cursor.next()
    last_processed_block_number = int(last_block["block_number"])
    logger.info("Last processed block: %s", last_processed_block_number)
    return last_processed_block_number - 100


async def process_block(
    collection: AsyncIOMotorCollection,
    session: AsyncIOMotorClientSession,
    raw_block: dict,
) -> None:
    block_number = raw_block["block_height"]
    block_hash = raw_block["block_hash"]
    items = [dict(_id=block_hash, block_number=block_number)]
    await mongo_insert_many(collection, session, items)


async def block_hash_to_number_mapper(start_block_height: Optional[int] = None) -> None:
    collection, session = await mongo_init("block_hash_to_number")
    # TODO paralelize
    # TODO handle chain reorgs
    # TODO terminate sessions and connections

    if start_block_height is None:
        start_block_height = await get_last_processed_block_number(collection)

    async for raw_block in stream_new_blocks(
        start_block_height=int(start_block_height),
        sleep_interval_seconds=1,
        n_blocks_ahead=100,
        block_height_key="block_height",
    ):
        # TODO block_height_key should be getting from ENV or from parser! now its hardcoded for aptos
        logger.info(f"Processing block {int(raw_block['block_height']):,}")
        create_task_safely(process_block(collection, session, raw_block))
