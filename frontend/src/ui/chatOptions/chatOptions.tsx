import styles from './chatOptions.module.scss';
//import clsx from 'clsx';

import { Chat as ChatType } from '../../types';

//const cx = clsx.bind(styles);

interface ChatOptionsProps {
    chat: ChatType;
    updateChat: (chat: ChatType) => void;
}

export default function ChatOptions({chat, updateChat}: ChatOptionsProps) {

    return (
        <div className={styles.chatOptions}>
            <h1>Edit Chat</h1>
            <form className={styles.form}>
                <div className={styles.formItem}>
                    <label htmlFor="title">Title</label>
                    <input type="text" id="title" value={chat.title} onChange={(e) => updateChat({...chat, title: e.target.value})} />
                </div>
                {chat.system_prompt && <div className={styles.formItem}>
                    <label htmlFor="systemPrompt">System Prompt</label>
                    <textarea id="systemPrompt" value={chat.system_prompt ?? ''} onChange={(e) => updateChat({...chat, system_prompt: e.target.value })} />
                </div>}
            </form>

        </div>
    );
}

