import { useCallback, useEffect, useState } from 'react';
import styles from './chat.module.scss';
import clsx from 'clsx';
import { ArrowUp } from '../assets/icons';
import { useNavigate, useParams } from 'react-router-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useEditChat, useGetChat, useGetModels, useSendMessage, useSendMessageStream } from '../../hooks';
import ChatOptions from '../chatOptions/chatOptions';
import { Chat as ChatType, MessageView } from '../../types';
import { useQueryClient } from 'react-query';
import { faCopy } from '@fortawesome/free-solid-svg-icons/faCopy';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

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
            node.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'});
        }
    }, []);
    
    const { chatId } = useParams();

    const queryClient = useQueryClient();
    const {isLoading: chatIsLoading, isError: chatIsError, error: chatError, data: chat } = useGetChat(chatId!);
    const {isLoading: modelsAreLoading, data: models} = useGetModels();

    const navigate = useNavigate();

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

    useEffect(() => {
        if (models) {
            const usableModels = models.filter(m => !m.requires_key || m.user_has_key);
            if (usableModels.length === 0) {
                navigate('/user/');
            }
        }
    }, [models, navigate]);

    const {sendMessage: sendMessageStream, response: messageResponse, loading: messageStreamLoading, sentMessage} = useSendMessageStream(chatId!);
    const sendMessageMutation = useSendMessage(chatId!);
    const editChatMutation = useEditChat(true, false);

    const handleSend = async () => {
        if (!chat || !models) return;

        if (input.trim() !== '') {
            let editedChat = chat;
            if (editing) {
                editedChat = await editChatMutation.mutateAsync(editing);
                setEditing(null);
            }
            const msg = input.trim();
            setInput('');
            // await sendMessageMutation.mutateAsync({
            //     role: 'user',
            //     content: msg
            // });
            const model = models.find(m => m.api_name === editedChat.default_model);
            if (!model) {
                console.error('Model not found');
                return;
            }
            if (model.supports_streaming) {
                await sendMessageStream({role: 'user', content: msg});
            } else {
                sendMessageMutation.mutate({role: 'user', content: msg});
            }
            void queryClient.invalidateQueries(chatId);
            setInput('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        e.stopPropagation();
        if (e.key === 'Enter' && !e.shiftKey) {
            void handleSend();
        }
    };

    const renderMessage = (message: MessageView, index: number, scroll?: boolean) => {
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
                
                <div className={cx(styles.info)}>
                        {message.role === 'assistant' && message.model && message.model !== chat?.default_model && <span className={styles.model}>Generated with {models?.find(m => m.api_name === message.model)?.human_name}</span>}
                        <button className={styles.copyButton} onClick={() => void navigator.clipboard.writeText(message.content)}>
                            <FontAwesomeIcon icon={faCopy} />
                        </button>
                </div>
                <div className={cx(styles.content)}>
                    {message.role === 'assistant' && <img className={styles.aiLogo} src='/ai-logo.svg' width={50} height={50} alt='AI'/>}
                    <div className={cx(styles.message)}>
                        <Markdown
                            children={message.content.replace('\\\\(', '$').replace('\\\\)', '$').replace('\\\\[', '$$').replace('\\\\]', '$$')}
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
                    </div>
                </div>
                
                
            </div>
        );
    };

    const renderLoadingMessage = () => {
        return <div className={cx(styles.messageContainer, styles.assistant)} ref={scrollToMessage}>
            <img className={styles.aiLogo} src='/ai-logo.svg' width={50} height={50} alt='AI'/>
            <div className={cx(styles.message, styles.loading)}>
                Loading...
            </div>
        </div>;
    }

    const renderInput = () => {
        return <div className={styles.inputContainer}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className={styles.input}
            placeholder="Type a message..."
          />
          <button onClick={() => void handleSend()} className={styles.button}>
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
                updateChat={(updateFn) => setEditing(c => c === null ? null : updateFn(c))} // this check is needed for typescript but editing will never actually be null here
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
            {sendMessageMutation.isLoading && sendMessageMutation.variables && renderMessage(sendMessageMutation.variables, messages.length)}
            {sendMessageMutation.isLoading && renderLoadingMessage()}
            {messageStreamLoading && sentMessage && renderMessage(sentMessage, messages.length)}
            {messageStreamLoading && messageResponse && renderMessage(messageResponse, messages.length + 1, true)}
        </div>
        {renderInput()}
      </div>
    );
}