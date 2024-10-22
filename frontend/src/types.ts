export type Role = 'user' | 'assistant' | 'system' | 'tool';

export type MessageContentTypeEnum = 'text' | 'image' | 'tool_call' | 'tool_result';

export interface MessageContent {
    type: MessageContentTypeEnum;
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
    tool_call_id: string;
}

interface ToolCall {
    name: string;
    args: Record<string, string | number>;
}

export interface ToolCallMessageContent extends MessageContent {
    type: 'tool_call';
    content: ToolCall;
    tool_call_id: string;
}

export type MessageContentType = TextMessageContent | ImageMessageContent | ToolCallMessageContent | ToolResultMessageContent;

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
    contents: (TextMessageContent | ImageMessageContent | ToolCallMessageContent | ToolResultMessageContent)[];
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
    tools?: string[];
}

export const MODEL_API_PROVIDERS = ['OPENAI', 'ANTHROPIC'] as const;

export const TOOL_API_PROVIDERS = ['TAVILY'] as const;

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