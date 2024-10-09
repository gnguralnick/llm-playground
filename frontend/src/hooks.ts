import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Message, Chat, Model, MessageView, User, ModelAPIKey } from './types';
import { useContext, useState } from 'react';
import UserContext, { UserContextType } from './context/userContext';

export async function backendFetch(url: string, options?: RequestInit, token?: string): Promise<Response> {
    const response = await fetch(import.meta.env.VITE_BACKEND_URL + url, {
        ...options,
        headers: {
            ...(options?.headers ?? {}),
            'Authorization': token ? `Bearer ${token}` : ''
        }
    });
    if (!response.ok) {
        throw new Error(response.statusText);
    }

    return response;
}

export function useUser(): UserContextType {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUser must be used within a UserProvider');
    }
    return context;
}

export function useGetUser(token?: string) {
    return useQuery({
        queryKey: ['user', {token}],
        queryFn: async ({queryKey}) => {
            const [, {token}] = queryKey as [string, {token?: string}];
            if (!token) {
                return null;
            }
            const response = await backendFetch('/users/me', undefined, token);
            const json: unknown = await response?.json();
            const user: User = json as User;
            return user;
        },
        enabled: false,
    });
}

export function useGetChat(chatId: string) {
    const { token } = useUser();
    return useQuery({
        queryKey: chatId,
        queryFn: async () => {
            const response = await backendFetch(`/chat/${chatId}`, undefined, token);
            const json: unknown = await response?.json();
            const chat: Chat = json as Chat;
            return chat;
        }
    });
}

export function useGetChats(userId: string) {
    const { token } = useUser();
    return useQuery({
        queryKey: userId,
        queryFn: async () => {
            const response = await backendFetch(`/chat/`, undefined, token);
            const json: unknown = await response?.json();
            const chats: Chat[] = json as Chat[];
            return chats;
        }
    });
}

export function useSendMessage(chatId: string) {
    const queryClient = useQueryClient();
    const { token } = useUser();
    return useMutation({
        mutationFn: async (msg: MessageView) => {
            const response = await backendFetch(`/chat/${chatId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(msg)
            }, token);
            const json: unknown = await response.json();
            return json as Message;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries(chatId);
        }
    });
}

export function useSendMessageStream(chatId: string) {
    const [done, setDone] = useState(false);
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<MessageView | null>(null);
    const [sentMessage, setSentMessage] = useState<MessageView | null>(null);
    const { token } = useUser();

    const sendMessage = async (msg: MessageView) => {
        setLoading(true);
        setSentMessage(msg);
        setResponse({role: 'assistant', contents: [{ type: 'text', content: ''}]});
        const response = await backendFetch(`/chat/${chatId}/stream/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(msg)
        }, token);
        const reader = response.body?.getReader();
        if (!reader) {
            setLoading(false);
            setDone(true);
            return;
        }
        const decoder = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }
            
            const result = decoder.decode(value);
            setResponse(r => {
                if (!r) {
                    return null;
                }
                return {
                    role: 'assistant', 
                    contents: [
                        {...r.contents[0], 
                            content: (r.contents[0].content ?? '') + result
                        }
                    ]
                };
            });
        }
        setLoading(false);
        setDone(true);
    };

    return {sendMessage, response, loading, done, sentMessage};
}

export function useCreateChat(navigate?: (url: string) => void) {
    const queryClient = useQueryClient();
    const { token } = useUser();
    return useMutation({
        mutationFn: async () => {
            const response = await backendFetch(`/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: 'New Chat'})
            }, token);
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
    const { token } = useUser();
    return useMutation({
        mutationFn: async (chat: Chat) => {
            const response = await backendFetch(`/chat/${chat.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chat)
            }, token);
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
    const { token, user } = useUser();
    return useMutation({
        mutationFn: async (chat: Chat) => {
            const response = await backendFetch(`/chat/${chat.id}/`, {
                method: 'DELETE'
            }, token);
            const json: unknown = await response.json();
            return json;
        },
        onSuccess: (_data, chat) => {
            void queryClient.invalidateQueries(user.id);
            if (navigate && currentChatId === chat.id) {
                navigate('/');
            }
        }
    });
}

export function useGetModels() {
    const { token } = useUser();
    return useQuery({
        queryKey: 'models',
        queryFn: async () => {
            const response = await backendFetch(`/models/`, undefined, token);
            const json: unknown = await response?.json();
            const models: Model[] = json as Model[];
            return models;
        }
    });
}

export function useGetAPIKeys() {
    const { token, user } = useUser();
    return useQuery({
        queryKey: user.id + '/api_key',
        queryFn: async () => {
            const response = await backendFetch('/users/me/api_key/', undefined, token);
            const json: unknown = await response.json();
            const keys: ModelAPIKey[] = json as ModelAPIKey[];
            return keys;
        }
    })
}

export function useAddAPIKey() {
    const { token, user } = useUser();
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({provider, key}: {provider: string, key: string}) => {
            const response = await backendFetch('/users/me/api_key/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({provider, key})
            }, token);

            const json: unknown = await response.json();
            return json as ModelAPIKey;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries(user.id + '/api_key');
        }
    })
}

export function useDeleteAPIKey() {
    const { token, user } = useUser();
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (provider: string) => {
            const response = await backendFetch(`/users/me/api_key/${provider}/`, {
                method: 'DELETE'
            }, token);
            const json: unknown = await response.json();
            return json;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries(user.id + '/api_key');
        }
    });
}