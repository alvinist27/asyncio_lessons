import asyncio

from graphic_chat import choices

QueuesType = dict[choices.QueueNames, asyncio.Queue]
