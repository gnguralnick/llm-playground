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

export type Role = 'user' | 'assistant' | 'system';

export type MessageContentType = 'text' | 'image';

export interface MessageContent {
    type: MessageContentType;
    content: string;
}

export interface TextMessageContent extends MessageContent {
    type: 'text';
}

export interface ImageMessageContent extends MessageContent {
    type: 'image';
    image_type: string;
}

export interface Message {
    role: Role;
    contents: (TextMessageContent | ImageMessageContent)[];
    id: string;
    model?: string;
    config?: Record<string, RangedNumber>;
}

export type MessageView = Pick<Message, "contents" | "role"> & Partial<Message>;

export interface Chat {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
    system_prompt?: string;
    default_model: string;
    config: Record<string, RangedNumber | OptionedString>;
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
    config: Record<string, RangedNumber>;
    requires_key: boolean;
    user_has_key: boolean;
}