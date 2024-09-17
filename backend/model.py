from openai import OpenAI
from data.schemas import Chat, MessageCreate, Role

client = OpenAI()

def generate_completion(chat: Chat, message: MessageCreate) -> MessageCreate:
    completion = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': m.role, 'content': m.content} for m in chat.messages] + [message.model_dump()]
    )
    
    return MessageCreate(role=Role.ASSISTANT, content=completion.choices[0].message.content)