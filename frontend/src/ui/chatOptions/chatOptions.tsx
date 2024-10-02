import styles from './chatOptions.module.scss';
//import clsx from 'clsx';

import { Chat as ChatType, Model, RangedNumber } from '../../types';

import Select from 'react-select';
import { useEffect } from 'react';

//const cx = clsx.bind(styles);

interface ChatOptionsProps {
    chat: ChatType;
    updateChat: (chat: ChatType | ((v: ChatType) => ChatType)) => void;
    models?: Model[];
    modelsLoading: boolean;
}

export default function ChatOptions({chat, updateChat, models, modelsLoading}: ChatOptionsProps) {

    const modelOptions = models?.map(m => ({label: m.human_name, value: m.api_name})) ?? [{label: 'Loading', value: 'Loading'}];
    let modelValue = undefined;
    if (models && chat.default_model) {
        modelValue = {label: models.find(m => m.api_name === chat.default_model)?.human_name, value: chat.default_model};
    }

    useEffect(() => {
        if (models) {
            // check if chat's config matches the selected model in terms of keys (in case the model was changed)
            const model = models.find(m => m.api_name === chat.default_model);
            if (!model) return;
            for (const key of Object.keys(chat.config)) {
                if (model.config[key] === undefined) {
                    updateChat((v: ChatType) => ({...v, config: model.config}));
                    break;
                }
            }
        }
    }, [models, chat.default_model, chat.config, updateChat]);

    const renderConfigItem = (key: string, index: number) => {
        const configItem = chat.config[key] as RangedNumber;

        if (!configItem) return null;
        
        if (configItem.max === null || configItem.min === null) {
            return <div key={index} className={styles.formItem}>
                <label htmlFor={key}>{key.replace(/_/g, ' ')}</label>
                <input 
                    type="number"
                    id={key} 
                    min={configItem.min ?? undefined}
                    max={configItem.max ?? undefined}
                    value={configItem.val} 
                    onChange={(e) => updateChat({...chat, config: {...chat.config, [key]: {...configItem, val: parseFloat(e.target.value)}}})}
                    />
            </div>;
        }
        const step = configItem.type === 'int' ? 1 : 0.01;
        const percent = (configItem.val - configItem.min) / (configItem.max - configItem.min) * 100;
        return <div key={index} className={styles.formItem}>
            <label htmlFor={key}>{key.replace(/_/g, ' ')}</label>
            <div className={styles.rangeCtr}>
                <span>{configItem.min}</span>
                <div className={styles.rangeWrapper}>
                    <input 
                        type="range"
                        id={key} 
                        min={configItem.min ?? -Infinity} 
                        max={configItem.max ?? Infinity} 
                        step={step} 
                        value={configItem.val} 
                        onChange={(e) => updateChat({...chat, config: {...chat.config, [key]: {...configItem, val: parseFloat(e.target.value)}}})}
                        />
                    <span style={{position: 'absolute', bottom: 0, left: `${percent}%`, transform: 'translateX(-25%)'}}>{configItem.val}</span>
                </div>
                <span>{configItem.max}</span>
            </div>

        </div>
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
                    {chat.messages && chat.messages.length > 1 && <p className={styles.notice}>Note: Changing the system prompt will not affect existing messages</p>}
                    <textarea id="systemPrompt" value={chat.system_prompt ?? ''} onChange={(e) => updateChat({...chat, system_prompt: e.target.value })} />
                </div>}
                <div className={styles.formItem}>
                    <label htmlFor="model">Model</label>
                    <Select
                        id="model"
                        options={modelOptions}
                        className={styles.select}
                        isDisabled={modelsLoading}
                        classNames={{
                            option: (state) => state.isSelected ? (styles.selected + ' ' + styles.option) : styles.option
                        }}
                        value={modelValue}
                        onChange={(selected) => updateChat({...chat, default_model: selected?.value ?? ''})}
                    />
                </div>
                {models && Object.keys(chat.config).map(renderConfigItem)}
            </form>

        </div>
    );
}

