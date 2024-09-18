import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Message, Chat, validateMessage } from './types';
import { validateChat } from './types';

async function backendFetch(url: string, options?: RequestInit) {
    const response = await fetch(import.meta.env.VITE_BACKEND_URL + url, options);
    if (!response.ok) {
        throw new Error(response.statusText);
    }

    return response;
}

export function useGetChat(chatId: string) {
    return useQuery({
        queryKey: chatId,
        queryFn: async () => {
            const response = await backendFetch(`/chat/${chatId}`);
            const json: unknown = await response?.json();
            validateChat(json);
            const chat: Chat = json;
            return chat;
        }
    });
}

export function useGetChats(userId: string) {
    return useQuery({
        queryKey: userId,
        queryFn: async () => {
            const response = await backendFetch(`/chat/`);
            const json: unknown = await response?.json();
            if (!Array.isArray(json)) {
                throw new Error('Invalid chat data');
            }
            for (const chat of json) {
                validateChat(chat);
            }
            const chats: Chat[] = json as Chat[];
            return chats;
        }
    });
}

export function useSendMessage(chatId: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (msg: Pick<Message, "content" | "role"> & Partial<Message>) => {
            const response = await backendFetch(`/chat/${chatId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(msg)
            });
            const json: unknown = await response.json();
            validateMessage(json);
            return json;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries(chatId);
        }
    });
}

export function useCreateChat(navigate?: (url: string) => void) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async () => {
            const response = await backendFetch(`/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: 'New Chat'})
            });
            const json: unknown = await response.json();
            validateChat(json);
            return json;
        },
        onSuccess: (data: Chat) => {
            void queryClient.invalidateQueries(data.user_id);
            if (navigate) {
                navigate(`/chat/${data.id}`);
            }
        }
    });
}

export function useEditChat() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (chat: Chat) => {
            const response = await backendFetch(`/chat/${chat.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chat)
            });
            const json: unknown = await response.json();
            validateChat(json);
            return json;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries();
        }
    });
}

export function useDeleteChat() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (chat: Chat) => {
            const response = await backendFetch(`/chat/${chat.id}`, {
                method: 'DELETE'
            });
            const json: unknown = await response.json();
            validateChat(json);
            return json;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries();
        }
    });
}