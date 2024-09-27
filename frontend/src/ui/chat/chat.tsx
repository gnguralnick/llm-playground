import { useCallback, useEffect, useState } from 'react';
import styles from './chat.module.scss';
import clsx from 'clsx';
import { ArrowUp } from '../assets/icons';
import { useParams } from 'react-router-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useEditChat, useGetChat, useGetModels, useSendMessageStream } from '../../hooks';
import ChatOptions from '../chatOptions/chatOptions';
import { Chat as ChatType } from '../../types';
import { useQueryClient } from 'react-query';

const cx = clsx.bind(styles);

function ChatLoading() {
    return (
        <div className={styles.chatContainer}>
            <div className={styles.messagesContainer}>
                {Array.from(Array(10).keys()).map((index) => (
                    <div key={index} className={cx(styles.messageContainer, {
                        [styles.user]: index % 2 === 0,
                        [styles.assistant]: index % 2 === 1
                    })}>
                        <div className={styles.messageLoading} />
                    </div>
                ))}
            </div>
            <div className={styles.inputContainer}>
                <input type="text" className={styles.input} placeholder="Type a message..." disabled />
                <button className={styles.button} disabled>
                    <ArrowUp />
                </button>
            </div>
        </div>
    );
}

export default function Chat() {
    const [input, setInput] = useState('');
    const [showSystem, setShowSystem] = useState(false);
    const [editing, setEditing] = useState<ChatType | null>(null);
    const scrollToMessage = useCallback((node: HTMLDivElement) => {
        if (node !== null) {
            node.scrollIntoView({behavior: 'smooth'});
        }
    }, []);
    
    const { chatId } = useParams();

    const queryClient = useQueryClient();
    const {isLoading: chatIsLoading, isError: chatIsError, error: chatError, data: chat } = useGetChat(chatId!);
    const {isLoading: modelsAreLoading, data: models} = useGetModels();

    const setEditingChat = (chat: ChatType) => {
        setEditing({...chat, system_prompt: chat.messages?.find(m => m.role === 'system')?.content});
    }

    useEffect(() => {
        if (chat?.messages?.length === 0 || (chat?.messages?.length === 1 && chat?.messages[0]?.role === 'system')) {
            setEditingChat(chat);
        }
    }, [chat]);

    useEffect(() => {
        setEditing(null);
    }, [chatId]);

    const {sendMessage: sendMessageStream, response: messageResponse, loading: messageStreamLoading, sentMessage} = useSendMessageStream(chatId!);
    const editChatMutation = useEditChat(true, false);

    const handleSend = async () => {
        if (input.trim() !== '') {
            if (editing) {
                await editChatMutation.mutateAsync(editing);
                setEditing(null);
            }
            const msg = input.trim();
            setInput('');
            // await sendMessageMutation.mutateAsync({
            //     role: 'user',
            //     content: msg
            // });
            await sendMessageStream({role: 'user', content: msg});
            void queryClient.invalidateQueries(chatId);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            void handleSend();
        }
    };

    const renderMessage = (message: {role: string, content: string}, index: number, scroll?: boolean) => {
        if (message.role === 'system') {
            return <div key={index} className={cx(styles.messageContainer, styles.system)}>
                <button onClick={() => setShowSystem(!showSystem)} className={styles.systemButton}>
                    {showSystem ? 'Hide' : 'Show'} System Prompt
                </button>
                {showSystem && message.content}
            </div>;
        }

        return (
            <div key={index} className={cx(styles.messageContainer, {
                    [styles.user]: message.role === 'user',
                    [styles.assistant]: message.role === 'assistant'
            })} ref={scroll ? scrollToMessage : undefined}>
                {message.role === 'assistant' && <img className={styles.aiLogo} src='/ai-logo.svg' width={50} height={50} alt='AI'/>}
                <div className={cx(styles.message)}>
                    {message.role === 'assistant' ? <Markdown
                        children={message.content}
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                        className={styles.markdown}
                        components={{
                        code(props) {
                            const {children, className, ...rest} = props
                            const match = /language-(\w+)/.exec(className ?? '')
                            return match ? (
                            <SyntaxHighlighter
                                PreTag="div"
                                children={String(children).replace(/\n$/, '')}
                                language={match[1]}
                                style={materialDark}
                            />
                            ) : (
                            <code {...rest} className={className}>
                                {children}
                            </code>
                            )
                        }
                        }}/>
                    : message.content}
                </div>
            </div>
        );
    };

    const renderInput = () => {
        return <div className={styles.inputContainer}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className={styles.input}
            placeholder="Type a message..."
          />
          <button onClick={() => handleSend} className={styles.button}>
            <ArrowUp />
          </button>
        </div>;
    }

    if (chatIsLoading || !chat) {
        return <ChatLoading />
    }

    if (chatIsError) {
        return <div>{(chatError as Error)?.message || (chatError as { statusText: string })?.statusText}</div>;
    }

    const messages = chat.messages ?? [];

    if (editing) {
        return <div className={styles.chatContainer}>
            <ChatOptions 
                chat={editing} 
                updateChat={setEditing}
                modelsLoading={modelsAreLoading}
                models={models}
                />
            {renderInput()}
        </div>;
    }

  
    return (
      <div className={styles.chatContainer}>
        <div className={styles.header}>
            <h1>{chat.title}</h1>
            <h2>{models?.find(m => chat.default_model === m.api_name)?.human_name}</h2>
            <button className={styles.editButton} onClick={() => setEditingChat(chat)}>Edit</button>
        </div>
        <div className={styles.messagesContainer}>
            {messages.length > 0 && messages.map((msg, index) => renderMessage(msg, index))}
            {/* {sendMessageMutation.isLoading && sendMessageMutation.variables && renderMessage(sendMessageMutation.variables, messages.length)}
            {sendMessageMutation.isLoading && !sendMessageMutation.variables && renderLoadingMessage()} */}
            {messageStreamLoading && sentMessage && renderMessage(sentMessage, messages.length)}
            {messageStreamLoading && messageResponse && renderMessage(messageResponse, messages.length + 1, true)}
        </div>
        {renderInput()}
      </div>
    );
}