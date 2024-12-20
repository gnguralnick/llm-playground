import styles from './chatOptions.module.scss';

import { Chat as ChatType, Model, OptionedString, RangedNumber, ToolConfig } from '../../types';

import Select from 'react-select';
import { useEffect } from 'react';

type UpdateChatType = ((updateFn: (currentChat: ChatType) => ChatType) => void);

interface ChatOptionsProps {
    chat: ChatType;
    updateChat: UpdateChatType;
    models?: Model[];
    tools?: ToolConfig[];
    modelsLoading: boolean;
}

export default function ChatOptions({chat, updateChat, tools, models, modelsLoading}: ChatOptionsProps) {

    const modelOptions = models?.filter(m => !m.requires_key || m.user_has_key).map(m => ({label: m.human_name, value: m.api_name})) ?? [{label: 'Loading', value: 'Loading'}];
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
                    // if the chat has a key that the model doesn't, reset the chat's config to the model's default config
                    // this could be improved by only removing the key that doesn't match, though different models may have different meanings for the same key
                    // so it's probably best to just reset the whole config
                    updateChat((v: ChatType): ChatType => ({...v, config: model.config}));
                    break;
                }
            }

            if (model.supports_tools && chat.config.tools !== undefined && chat.config.tools.length > 0 && chat.tools === undefined) {
                updateChat((v: ChatType): ChatType => ({...v, tools: chat.config.tools?.map(tool => tool.name)}));
            } else if (!model.supports_tools && chat.tools !== undefined) {
                // remove tools from chat if the model doesn't support them
                updateChat((v: ChatType): ChatType => ({...v, tools: undefined}));
            }
        }
    }, [models, chat.default_model, chat.config, updateChat, chat.tools]);

    const renderConfigItem = (key: string, index: number) => {
        const configItem = chat.config[key];

        if (!configItem) return null;

        if (configItem.type === 'string') {
            return renderOptionedStringConfigItem(key, index, configItem);
        } else if (configItem.type === 'int' || configItem.type === 'float') {
            return renderNumberConfigItem(key, index, configItem);
        } else {
            return null;
        }
    };

    const renderNumberConfigItem = (key: string, index: number, configItem: RangedNumber) => {
        if (configItem.max === null || configItem.min === null) {
            return <div key={index} className={styles.formItem}>
                <label htmlFor={key}>{key.replace(/_/g, ' ')}</label>
                <input 
                    type="number"
                    id={key} 
                    min={configItem.min ?? undefined}
                    max={configItem.max ?? undefined}
                    value={configItem.val} 
                    onChange={(e) => updateChat(c => ({...c, config: {...c.config, [key]: {...configItem, val: parseFloat(e.target.value)}}}))}
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
                        onChange={(e) => updateChat(c => ({...c, config: {...c.config, [key]: {...configItem, val: parseFloat(e.target.value)}}}))}
                        />
                    <span style={{position: 'absolute', bottom: 0, left: `${percent}%`, transform: 'translateX(-25%)'}}>{configItem.val}</span>
                </div>
                <span>{configItem.max}</span>
            </div>

        </div>
    }

    const renderOptionedStringConfigItem = (key: string, index: number, configItem: OptionedString) => {
        return <div key={index} className={styles.formItem}>
            <label htmlFor={key}>{key.replace(/_/g, ' ')}</label>
            <Select
                id={key}
                options={configItem.options.map(o => ({label: o, value: o}))}
                className={styles.select}
                classNames={{
                    option: (state) => state.isSelected ? (styles.selected + ' ' + styles.option) : styles.option
                }}
                value={{label: configItem.val, value: configItem.val}}
                onChange={(selected) => updateChat(c => ({...c, config: {...c.config, [key]: {...configItem, val: selected?.value ?? ''}}}))}
            />
        </div>
    }

    const renderToolConfigItem = (tool: ToolConfig, index: number) => {
        return <div key={index} className={styles.tool}>
            <div className={styles.inputGroup}>
                <label htmlFor={tool.name}>{tool.name}</label>
                <input type='checkbox' id={tool.name} checked={(chat.tools ?? []).includes(tool.name)} onChange={(e) => {
                    if (e.target.checked) {
                        updateChat(c => ({...c, tools: [...(c.tools ?? []), tool.name]}));
                    } else {
                        updateChat(c => ({...c, tools: (c.tools ?? []).filter(t => t !== tool.name)}));
                    }
                }} />
            </div>
            <p>{tool.description}</p>
        </div>
    }
    
    return (
        <div className={styles.chatOptions}>
            <h1>Edit Chat</h1>
            <form className={styles.form}>
                <div className={styles.formItem}>
                    <label htmlFor="title">Title</label>
                    <input type="text" id="title" value={chat.title} onChange={(e) => updateChat(c => ({...c, title: e.target.value}))} />
                </div>
                {chat.system_prompt && <div className={styles.formItem}>
                    <label htmlFor="systemPrompt">System Prompt</label>
                    {chat.messages && chat.messages.length > 1 && <p className={styles.notice}>Note: Changing the system prompt will not affect existing messages</p>}
                    <textarea id="systemPrompt" value={chat.system_prompt ?? ''} onChange={(e) => updateChat(c => ({...c, system_prompt: e.target.value }))} />
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
                        onChange={(selected) => updateChat(c => ({...c, default_model: selected?.value ?? ''}))}
                    />
                </div>
                {models && Object.keys(chat.config).map(renderConfigItem)}
                {models?.find(m => m.api_name === chat.default_model)?.supports_tools && tools && <div className={styles.formGroup}>
                    <h2>Tools</h2>
                    {tools.map(renderToolConfigItem)}
                </div>}
            </form>

        </div>
    );
}

