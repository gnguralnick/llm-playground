from app.util import ModelConfigWithTools, RangedFloat, OptionedString, RangedInt


class OpenAIConfig(ModelConfigWithTools):
    frequency_penalty: RangedFloat = RangedFloat(min=-2, max=2, val=0)
    max_completion_tokens: RangedInt = RangedInt(min=1, max=None, val=1024)
    # n: RangedInt = RangedInt(min=1, max=None, val=1)
    presence_penalty: RangedFloat = RangedFloat(min=-2, max=2, val=0)
    temperature: RangedFloat = RangedFloat(min=0, max=2, val=1)
    top_p: RangedFloat = RangedFloat(min=0, max=1, val=1)
    image_detail: OptionedString = OptionedString(options=['auto', 'low', 'high'], val='auto')
    
    def dump_values(self) -> dict:
        return {
            'frequency_penalty': self.frequency_penalty.val,
            'max_completion_tokens': self.max_completion_tokens.val,
            # 'n': self.n.val,
            'presence_penalty': self.presence_penalty.val,
            'temperature': self.temperature.val,
            'top_p': self.top_p.val
        }