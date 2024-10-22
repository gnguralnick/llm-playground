import anthropic
from app.util import RangedFloat, RangedInt
from app.schemas.model_config import ModelConfig


class AnthropicConfig(ModelConfig):
    max_tokens: RangedInt = RangedInt(min=1, max=None, val=1024)
    temperature: RangedFloat = RangedFloat(min=0, max=1, val=1)
    top_k: int | None = None
    top_p: float | None = None
    
    def dump_values(self) -> dict:
        return {
            'max_tokens': self.max_tokens.val,
            'temperature': self.temperature.val,
            'top_k': self.top_k if self.top_k is not None else anthropic.NOT_GIVEN,
            'top_p': self.top_p if self.top_p is not None else anthropic.NOT_GIVEN
        }