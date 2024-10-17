from asyncio import Queue
from pydantic import UUID4
from collections import defaultdict


class ChatStreamManager:
    def __init__(self):
        # self.active_chats stores the token queue and the entire message sent so far
        self.active_chats: dict[UUID4, tuple[Queue, str]] = defaultdict(lambda : (Queue(), ''))
    
    def get_full_message(self, chat_id: UUID4) -> str:
        return self.active_chats[chat_id][1]
        
    def reset_chat(self, chat_id: UUID4):
        self.active_chats[chat_id] = (Queue(), '')
    
    def chat_has_message(self, chat_id: UUID4) -> bool:
        return self.active_chats[chat_id][0].qsize() > 0
        
    async def send_message(self, chat_id: UUID4, message: str):
        queue, current_message = self.active_chats[chat_id]
        self.active_chats[chat_id] = (queue, current_message + message)
        await queue.put(message)
        return
    
    async def end_message(self, chat_id: UUID4):
        queue, _ = self.active_chats[chat_id]
        await queue.put('END MESSAGE')
        return
    
    async def consume_message(self, chat_id: UUID4) -> str:
        queue, _ = self.active_chats[chat_id]
        message = await queue.get()
        return message