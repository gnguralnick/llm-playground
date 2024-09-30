export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    id: string;
    model?: string;
}

export type MessageView = Pick<Message, "content" | "role"> & Partial<Message>;

export interface Chat {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
    system_prompt?: string;
    default_model: string;
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
}