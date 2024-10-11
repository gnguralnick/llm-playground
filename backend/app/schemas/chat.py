from pydantic import BaseModel, UUID4
import datetime
from app.schemas.message import MessageView
from app.chat_models import model_config_type
from app.chat_models.openai_model import OpenAIConfig

class Chat(BaseModel):
    title: str
    default_model: str = 'gpt-4o-mini'
    config: model_config_type = OpenAIConfig()
    
class ChatCreate(Chat):
    system_prompt: str = """You are a helpful assistant. Format responses using Markdown. 
    You may use latex by wrapping in $ symbols (for inline) or $$ symbols (for block).
    e.g $5 + 5 = 10$ or $$5 + 5 = 10$$
    You may also use a fenced code block with an info string of `math`:
    e.g. ```math
    L = \\frac{1}{2} \\rho v^2 S C_L
    ```
    DO NOT use brackets or parentheses to denote latex; you MUST use $ or $$.
    DO NOT insert any unnecessary backslashes (\\) in your latex.
    """
    
class ChatView(Chat):
    id: UUID4
    user_id: UUID4
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True

class ChatFull(ChatView):
    messages: list[MessageView] = []
    
    class Config:
        orm_mode = True
        
