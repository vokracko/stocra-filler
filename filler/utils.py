import asyncio
from logging import getLogger
from typing import AsyncIterable, Coroutine, Iterable, Mapping, Tuple

from genesis.blockchain.exceptions import DoesNotExist, UnableToLoadDataFromStorage
from genesis.blockchain.factory import NodeAdapterFactory
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
)
from pymongo.errors import BulkWriteError

from filler.config import CONFIG

logger = getLogger(__name__)


async def get_block(block_height: int):
    return await CONFIG.adapter.get_block_by_height(height=block_height)


async def stream_new_blocks(
    start_block_height: int,
    sleep_interval_seconds: int,
    n_blocks_ahead: int,
    block_height_key: str,
) -> AsyncIterable[dict]:
    block_dict = await get_block(block_height=start_block_height)
    first_block_to_load_height = int(block_dict[block_height_key]) + 1
    last_block_to_load_height = first_block_to_load_height + n_blocks_ahead + 1
    yield block_dict

    block_tasks = [
        asyncio.create_task(get_block(block_height=height))
        for height in range(first_block_to_load_height, last_block_to_load_height)
    ]

    while True:
        block_task = block_tasks.pop(0)
        try:
            await asyncio.wait_for(block_task, timeout=None)
            yield block_task.result()
        except asyncio.TimeoutError:
            block_tasks.insert(0, asyncio.create_task(get_block(first_block_to_load_height)))
            continue
        except DoesNotExist:
            await asyncio.sleep(sleep_interval_seconds)
            block_tasks.insert(0, asyncio.create_task(get_block(first_block_to_load_height)))
            continue
        except UnableToLoadDataFromStorage:
            logger.exception("Unable to load data from storage")

        block_tasks.append(asyncio.create_task(get_block(last_block_to_load_height)))
        first_block_to_load_height += 1
        last_block_to_load_height += 1


async def mongo_init(collection_name: str) -> Tuple[AsyncIOMotorCollection, AsyncIOMotorClientSession]:
    CONFIG.adapter = await NodeAdapterFactory.get_client(
        CONFIG.node_blockchain, url=CONFIG.node_url, token=CONFIG.node_token
    )
    client = AsyncIOMotorClient(f"{CONFIG.node_blockchain.blockchain_name}-mongo-1")
    database = client["stocra"]
    collection = database[collection_name]
    session = await client.start_session()
    return collection, session


async def mongo_insert_many(
    collection: AsyncIOMotorCollection,
    session: AsyncIOMotorClientSession,
    items: Iterable[Mapping],
):
    try:
        await collection.insert_many(items, ordered=False, session=session)
    except BulkWriteError as exc:
        for error in exc.details["writeErrors"]:
            await collection.replace_one(filter=error["keyValue"], replacement=error["op"])


ABANDONED_TASKS = set()


def create_task_safely(coroutine: Coroutine) -> None:
    task = asyncio.create_task(coroutine)
    ABANDONED_TASKS.add(task)
    task.add_done_callback(ABANDONED_TASKS.discard)
