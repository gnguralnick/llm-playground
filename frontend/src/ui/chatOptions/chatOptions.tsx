import styles from './chatOptions.module.scss';
//import clsx from 'clsx';

import { Chat as ChatType, Model } from '../../types';

import Select from 'react-select';

//const cx = clsx.bind(styles);

interface ChatOptionsProps {
    chat: ChatType;
    updateChat: (chat: ChatType) => void;
    models?: Model[];
    modelsLoading: boolean;
}

export default function ChatOptions({chat, updateChat, models, modelsLoading}: ChatOptionsProps) {

    const modelOptions = models?.map(m => ({label: m.human_name, value: m.api_name})) ?? [{label: 'Loading', value: 'Loading'}];
    let modelValue = undefined;
    if (models && chat.default_model) {
        modelValue = {label: models.find(m => m.api_name === chat.default_model)?.human_name, value: chat.default_model};
    }
    
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
                <div className={styles.formItem}>
                    <label htmlFor="defaultModel">Default Model</label>
                    <Select
                        id="defaultModel"
                        options={modelOptions}
                        isDisabled={modelsLoading}
                        value={modelValue}
                        onChange={(selected) => updateChat({...chat, default_model: selected?.value ?? ''})}
                    />
                </div>
            </form>

        </div>
    );
}

