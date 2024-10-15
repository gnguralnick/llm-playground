export type Role = 'user' | 'assistant' | 'system';

export type MessageContentType = 'text' | 'image' | 'tool_use' | 'tool_result';

export interface MessageContent {
    type: MessageContentType;
    content: string | Record<string, string | number> | ToolCall;
}

export interface TextMessageContent extends MessageContent {
    type: 'text';
    content: string;
}

export interface ImageMessageContent extends MessageContent {
    type: 'image';
    image_type: string;
    image?: File;
    content: string;
}

export interface ToolResultMessageContent extends MessageContent {
    type: 'tool_result';
    content: Record<string, string | number>;
    tool_use_id: string;
}

interface ToolCall {
    name: string;
    args: Record<string, string | number>;
}

export interface ToolUseMessageContent extends MessageContent {
    type: 'tool_use';
    content: ToolCall;
    id: string;
}

export interface RangedNumber {
    type: 'float' | 'int';
    min: number | null;
    max: number | null;
    val: number;
}

export interface OptionedString {
    type: 'string';
    options: string[];
    val: string;
}

export interface ToolParameter {
    type: string
    description: string
    enum?: string[]
}

export interface ToolConfig {
    name: string
    description: string
    parameters: Record<string, ToolParameter>
    required: string[]
}

export type ModelConfig = Record<string, RangedNumber | OptionedString> & {tools?: ToolConfig[]};

export interface Message {
    role: Role;
    contents: (TextMessageContent | ImageMessageContent)[];
    id: string;
    model?: string;
    config?: ModelConfig;
}

export type MessageView = Pick<Message, "contents" | "role"> & Partial<Message>;

export interface Chat {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
    system_prompt?: string;
    default_model: string;
    config: ModelConfig;
}

export const MODEL_API_PROVIDERS = ['openai', 'anthropic'] as const;

export interface ModelAPIKey {
    provider: typeof MODEL_API_PROVIDERS[number];
}

export interface User {
    id: string;
    email: string;
    chats?: Chat[];
    api_keys: ModelAPIKey[];
}

export interface Model {
    human_name: string;
    api_name: string;
    supports_streaming: boolean;
    supports_images: boolean;
    supports_tools: boolean;
    config: ModelConfig;
    requires_key: boolean;
    user_has_key: boolean;
}