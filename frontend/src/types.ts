export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    id: string;
    model?: string;
}

export interface Chat {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
    system_prompt?: string;
    default_model: string;
}

export interface User {
    id: string;
    email: string;
    chats?: Chat[];
}

export interface Model {
    human_name: string;
    api_name: string;
}