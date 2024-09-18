export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    id: string;
}

export interface Chat {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
    system_prompt?: string;
}

export interface User {
    id: string;
    email: string;
    chats?: Chat[];
}