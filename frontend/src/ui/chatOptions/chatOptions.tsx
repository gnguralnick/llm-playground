import { useEffect, useState } from 'react';
import styles from './chatOptions.module.scss';
//import clsx from 'clsx';

import { useParams } from 'react-router-dom';
import { Chat as ChatType } from '../../types';
import { useEditChat, useGetChat } from '../../hooks';

//const cx = clsx.bind(styles);

export default function ChatOptions() {

    const mutation = useEditChat();

    const { chatId } = useParams();

    const {isLoading, isError, error, data: originalChat} = useGetChat(chatId!);

    const [chat, setChat] = useState<ChatType | null>(null);

    const handleSave = (e: React.FormEvent) => {
        e.preventDefault();
        if (chat) {
            mutation.mutate(chat);
        }
    }

    useEffect(() => {
        if (originalChat) {
            setChat(originalChat);
        }
    }, [originalChat]);

    if (isLoading || !originalChat || !chat) {
        return <div>Loading...</div>;
    }

    if (isError) {
        return <div>{(error as Error)?.message || (error as { statusText: string })?.statusText}</div>;
    }

    return (
        <div className={styles.chatOptions}>
            <h1>Edit Chat</h1>
            <form className={styles.form}>
                <div className={styles.formItem}>
                    <label htmlFor="title">Title</label>
                    <input type="text" id="title" value={chat?.title} onChange={(e) => setChat({...chat, title: e.target.value})} />
                </div>
                <button className={styles.formSubmit} onClick={handleSave}>Save</button>
            </form>

        </div>
    );
}

