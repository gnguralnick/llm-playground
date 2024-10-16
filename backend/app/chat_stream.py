from asyncio import Queue
from pydantic import UUID4


class ChatStreamManager:
    def __init__(self):
        # self.active_chats stores the token queue and the entire message sent so far
        self.active_chats: dict[UUID4, tuple[Queue, str]] = {}
    
    def get_full_message(self, chat_id: UUID4) -> str:
        return self.active_chats[chat_id][1]
    
    def add_chat(self, chat_id: UUID4):
        self.active_chats[chat_id] = (Queue(), '')
        
    def remove_chat(self, chat_id: UUID4):
        del self.active_chats[chat_id]
    
    def chat_is_active(self, chat_id: UUID4) -> bool:
        return chat_id in self.active_chats
    
    def chat_has_message(self, chat_id: UUID4) -> bool:
        return self.active_chats[chat_id][0].qsize() > 0
        
    async def send_message(self, chat_id: UUID4, message: str):
        if chat_id in self.active_chats:
            queue, current_message = self.active_chats[chat_id]
            self.active_chats[chat_id] = (queue, current_message + message)
            await queue.put(message)
            return
        raise ValueError('Chat has no active queue')
    
    async def consume_message(self, chat_id: UUID4) -> str:
        if chat_id in self.active_chats:
            queue, _ = self.active_chats[chat_id]
            message = await queue.get()
            return message
        raise ValueError('Chat has no active queue')