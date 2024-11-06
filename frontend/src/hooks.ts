import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Message, Chat, Model, MessageView, User, ModelAPIKey, ToolConfig } from './types';
import { useContext, useEffect, useRef } from 'react';
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

export function useGetUser(token?: string, navigate?: (url: string) => void) {
    return useQuery({
        queryKey: ['user', {token}],
        queryFn: async ({queryKey}) => {
            const [, {token}] = queryKey as [string, {token?: string}];
            if (!token) {
                return null;
            }
            const response = await backendFetch('/users/me', undefined, token);
            if (!response.ok) {
                if (navigate) {
                    navigate('/login');
                }
                return null;
            }
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

function createMessageFormData(msg: MessageView): FormData {
    const formData = new FormData();
    const messageObj = {
        role: msg.role,
        contents: msg.contents.map(c => ({
            type: c.type,
            content: c.content,
            ...(c.type === 'image' || c.type === 'file') && {image_type: c.image_type},
        }))
    }
    formData.append('message', JSON.stringify(messageObj));
    msg.contents.filter(content => content.type === 'image').forEach(content => {
        if (content.image) {
            formData.append('files', content.image);
        }
    });
    msg.contents.filter(content => content.type === 'file').forEach(content => {
        if (content.file) {
            formData.append('files', content.file);
        }
    });
    return formData;
}

export function useSendMessage(chatId: string) {
    const queryClient = useQueryClient();
    const { token } = useUser();
    return useMutation({
        mutationFn: async (msg: MessageView) => {
            const formData = createMessageFormData(msg);
            const response = await backendFetch(`/chat/${chatId}/`, {
                method: 'POST',
                body: formData
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
    const { token } = useUser();

    const sendMessage = async (msg: MessageView) => {
        const formData = createMessageFormData(msg);
        await backendFetch(`/chat/${chatId}/stream/`, {
            method: 'POST',
            body: formData
        }, token);
    };

    return sendMessage;
}

export function useSubscribeToChat(chatId: string, onMessage: (msg: string) => void, onClose?: () => void) {
    const { token } = useUser();
    const connection = useRef<WebSocket | null>(null);
    useEffect(() => {
        const ws = new WebSocket(import.meta.env.VITE_WS_URL + `/chat/${chatId}/stream?token=${token}`);
        ws.onmessage = (event: MessageEvent<string>) => {
            onMessage(event.data);
        };

        ws.onclose = () => {
            if (onClose) {
                onClose();
            }
        };

        connection.current = ws;

        return () => {
            if (connection.current && connection.current.readyState === WebSocket.OPEN) {
                connection.current.close();
            }
        }
    }, [chatId, token, onMessage, onClose]);

    return connection;
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
            const response = await backendFetch(`/chat/${chat.id}`, {
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

export function useGetTools() {
    const { token } = useUser();
    return useQuery({
        queryKey: 'tools',
        queryFn: async () => {
            const response = await backendFetch(`/tools/`, undefined, token);
            const json: unknown = await response?.json();
            const tools: ToolConfig[] = json as ToolConfig[];
            return tools;
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

export function useRefreshSidebar() {
    const queryClient = useQueryClient();
    const { user } = useUser();

    function refreshSidebar() {
        void queryClient.invalidateQueries(user.id);
    }

    return refreshSidebar;
}