export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    id: string;
}

export function validateMessage(data: unknown): asserts data is Message {
    if (!(typeof data === 'object' && data !== null
        && 'role' in data && typeof data.role === 'string' 
        && ['user', 'assistant', 'system'].includes(data.role)
        && 'content' in data && typeof data.content === 'string'
        && 'id' in data && typeof data.id === 'string')) {
        throw new Error('Invalid message data');
    }
}

export interface Chat {
    id: string;
    user_id: string;
    title: string;
    messages?: Message[];
}

export function validateChat(data: unknown): asserts data is Chat {
    if (!(typeof data === 'object' && data !== null
        && 'id' in data && typeof data.id === 'string' 
        && 'user_id' in data && typeof data.user_id === 'string' 
        && 'title' in data && typeof data.title === 'string'
        && (!('messages' in data) || (Array.isArray(data.messages) && data.messages.every(validateMessage))))) {
        throw new Error('Invalid chat data');
    }
}

export interface User {
    id: string;
    email: string;
    chats?: Chat[];
}