import {NavLink, useParams, useNavigate} from 'react-router-dom';
import styles from './sidebar.module.scss';
import clsx from 'clsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faPencil } from '@fortawesome/free-solid-svg-icons';
import { Chat } from '../types';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useCallback, useEffect, useRef, useState } from 'react';


const cx = clsx.bind(styles);

interface SidebarProps {
    userId: string;
};

function SidebarLoading() {
    return (
        <div className={styles.sidebar}>
            <ul className={styles.chatsList}>
                {[1, 2, 3, 4, 5].map((index) => (
                    <li key={index} className={styles.chat}>
                        <div className={styles.loadingChat} />
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default function Sidebar({userId}: SidebarProps) {

    const { chatId: activeChat } = useParams();
    const queryClient = useQueryClient();
    const navigate = useNavigate();

    const [editing, setEditing] = useState<Chat | null>(null);
    const editInputRef = useRef<HTMLInputElement>(null);

    const { isLoading, isError, error, data } = useQuery({
        queryKey: userId,
        queryFn: async () => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/`);
            return (await response.json()) as Partial<Chat>[];
        }
    });

    const createChatMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: 'New Chat'})
            });
            return (await response.json()) as Chat;
        },
        onSuccess: (data: Chat) => {
            void queryClient.invalidateQueries(userId);
            navigate(`/chat/${data.id}`);
        }
    });

    const editChatMutation = useMutation({
        mutationFn: async (chat: Chat) => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/${chat.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chat)
            });
            return (await response.json()) as Chat;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries(userId);
        }
    });

    const onEditSubmit = useCallback(() => {
        if (!editing) { return; }
        editChatMutation.mutate(editing);
        setEditing(null);
    }, [editChatMutation, editing]);

    useEffect(() => {
        if (!editing) { return; }

        const handler = (e: MouseEvent) => {
            e.stopPropagation();
            if (editInputRef.current && !editInputRef.current.contains(e.target as Node)) {
                onEditSubmit();
            }
        };

        window.addEventListener('click', handler);

        return () => {
            window.removeEventListener('click', handler);
        };
    }, [editing, onEditSubmit]);

    if (isLoading) {
        return <SidebarLoading />;
    }

    if (isError) {
        return <div>{(error as Error)?.message || (error as { statusText: string })?.statusText}</div>;
    }

    const chats = data as Chat[];

    return (
        <div className={cx(styles.sidebar)}>
            <button className={styles.createChatButton} onClick={() => createChatMutation.mutate()}>
                <FontAwesomeIcon icon={faPlus} />
            </button>
            <ul className={styles.chatsList}>
                {chats.map((chat) => {
                    if (chat.id === editing?.id) {
                        return <li key={chat.id} className={styles.chat}>
                            <input type="text" value={editing.title} ref={editInputRef}
                                onChange={(e) => {
                                    setEditing({...editing, title: e.target.value});
                                }} 
                                onKeyDown={(e) => {
                                    e.stopPropagation();
                                    if (e.key === 'Enter') {
                                        onEditSubmit();
                                    }
                                }}
                            />
                        </li>;
                    }
                    return <NavLink to={`/chat/${chat.id}`} key={chat.id} className={cx(styles.chat, {
                        [styles.active]: chat.id === activeChat
                    })}>
                        <li className={styles.chatName}>
                            {chat.title}
                            <button className={styles.editBtn} onClick={(e) => {e.stopPropagation(); e.preventDefault(); setEditing(chat);}}>
                                <FontAwesomeIcon icon={faPencil} />
                            </button>
                        </li>
                    </NavLink>;
                })}
            </ul>
        </div>
    );
}

