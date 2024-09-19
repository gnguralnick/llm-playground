import {NavLink, useParams, useNavigate} from 'react-router-dom';
import styles from './sidebar.module.scss';
import clsx from 'clsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faPencil, faX } from '@fortawesome/free-solid-svg-icons';
import { Chat } from '../../types';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useCreateChat, useDeleteChat, useEditChat, useGetChats } from '../../hooks';


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
    const navigate = useNavigate();

    const [editing, setEditing] = useState<Chat | null>(null);
    const editInputRef = useRef<HTMLInputElement>(null);

    const { isLoading, isError, error, data: chats } = useGetChats(userId);

    const createChatMutation = useCreateChat(navigate);

    const editChatMutation = useEditChat();

    const deleteChatMutation = useDeleteChat(navigate, activeChat);

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

    if (isLoading || !chats) {
        return <SidebarLoading />;
    }

    if (isError) {
        return <div>{(error as Error)?.message || (error as { statusText: string })?.statusText}</div>;
    }

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
                        <li className={styles.chatNameCtr}>
                            <p className={styles.chatName}>
                                {chat.title}
                            </p>
                            <div className={styles.chatButtons}>
                                <button className={styles.chatBtn} onClick={(e) => {e.stopPropagation(); e.preventDefault(); setEditing(chat);}}>
                                    <FontAwesomeIcon icon={faPencil} />
                                </button>
                                <button className={styles.chatBtn} onClick={(e) => {e.stopPropagation(); e.preventDefault(); deleteChatMutation.mutate(chat);}}>
                                    <FontAwesomeIcon icon={faX} />
                                </button>
                            </div>

                        </li>
                    </NavLink>;
                })}
            </ul>
        </div>
    );
}

