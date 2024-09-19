import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Message, Chat, Model } from './types';

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
            const chat: Chat = json as Chat;
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
            return json as Message;
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
            return json as Chat;
        },
        onSuccess: (data: Chat) => {
            void queryClient.invalidateQueries(data.user_id);
            if (navigate) {
                navigate(`/chat/${data.id}`);
            }
        }
    });
}

export function useEditChat(invalidateUserQuery?: boolean, invalidateChatQuery?: boolean) {
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
            return json as Chat;
        },
        onSuccess: (data) => {
            if (invalidateChatQuery) {
                void queryClient.invalidateQueries(data.id);
            }
            if (invalidateUserQuery) {
                void queryClient.invalidateQueries(data.user_id);
            }
        }
    });
}

export function useDeleteChat(navigate?: (url: string) => void, currentChatId?: string) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (chat: Chat) => {
            const response = await backendFetch(`/chat/${chat.id}`, {
                method: 'DELETE'
            });
            const json: unknown = await response.json();
            return json;
        },
        onSuccess: (_data, chat) => {
            void queryClient.invalidateQueries(); // TODO: this should be invalidateQueries(userId)
            if (navigate && currentChatId === chat.id) {
                navigate('/');
            }
        }
    });
}

export function useGetModels() {
    return useQuery({
        queryKey: 'models',
        queryFn: async () => {
            const response = await backendFetch(`/models/`);
            const json: unknown = await response?.json();
            const models: Model[] = json as Model[];
            return models;
        }
    });
}