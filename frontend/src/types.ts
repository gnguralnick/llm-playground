export type Message = {
    role: 'user' | 'assistant' | 'system';
    content: string;
    id: string;
}

export type Chat = {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
}

export type User = {
    id: string;
    email: string;
    chats?: Chat[];
}