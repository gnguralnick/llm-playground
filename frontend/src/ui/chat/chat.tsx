import { useCallback, useEffect, useRef, useState } from 'react';
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
import { backendFetch, useEditChat, useGetChat, useGetModels, useGetTools, useRefreshSidebar, useSendMessage, useSendMessageStream, useSubscribeToChat, useUser } from '../../hooks';
import ChatOptions from '../chatOptions/chatOptions';
import { Chat as ChatType, ImageMessageContent, MessageContent, MessageView, TextMessageContent, ToolCallMessageContent } from '../../types';
import { useQueryClient } from 'react-query';
import { faCopy } from '@fortawesome/free-solid-svg-icons/faCopy';
import { faImage } from '@fortawesome/free-solid-svg-icons';
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
    const {token, user} = useUser();
    const [input, setInput] = useState('');
    const [imageInput, setImageInput] = useState<File | null>(null);
    const imageInputRef = useRef<HTMLInputElement>(null);
    const [showSystem, setShowSystem] = useState(false);
    const [editing, setEditing] = useState<ChatType | null>(null);
    const [images, setImages] = useState<Record<string, string>>({});
    const scrollToMessage = useCallback((node: HTMLDivElement) => {
        if (node !== null) {
            node.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'});
        }
    }, []);

    const [toolResultsShown, setToolResultsShown] = useState<Record<string, boolean>>({});
    
    const { chatId } = useParams();

    const queryClient = useQueryClient();
    const {isLoading: chatIsLoading, isError: chatIsError, error: chatError, data: chat } = useGetChat(chatId!);
    const {isLoading: modelsAreLoading, data: models} = useGetModels();
    const {data: tools} = useGetTools();
    const refreshSidebar = useRefreshSidebar();
    const [streamError, setStreamError] = useState<string | null>(null);

    const navigate = useNavigate();

    const setEditingChat = (chat: ChatType) => {
        setEditing({...chat, system_prompt: (chat.messages?.find(m => m.role === 'system')?.contents[0] as TextMessageContent).content});
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

    useEffect(() => {
        async function fetchImages() {
            if (chat?.messages) {
                for (const message of chat.messages) {
                    const imageContents = message.contents.filter(c => c.type === 'image');
                    const newImages = await imageContents.reduce(async (acc, content) => {
                        const response = await backendFetch('/' + content.content, undefined, token);
                        const blob = await response.blob();
                        const url = URL.createObjectURL(blob);
                        return {...(await acc), [content.content]: url};
                    }, Promise.resolve({}) as Promise<Record<string, string>>);
                    setImages(i => ({...i, ...newImages}));
                }
            }
        }
        void fetchImages();
    }, [chat, token]);

    const sendMessageStream = useSendMessageStream(chatId!);
    const sendMessageMutation = useSendMessage(chatId!);
    const editChatMutation = useEditChat(true, false);
    const [streamingMessage, setStreamingMessage] = useState('');
    useSubscribeToChat(chatId!, 
        useCallback((token) => {
            if (token === 'END MESSAGE') {
                setStreamingMessage('');
                void queryClient.invalidateQueries(chatId);
                void queryClient.invalidateQueries(user.id);
                return;
            }
            setStreamingMessage(msg => msg + token);
        }, [queryClient, chatId, user.id]),
    );

    const handleSend = async () => {
        if (!chat || !models) return;

        setStreamError(null);

        if (input.trim() !== '') {
            let editedChat = chat;
            if (editing) {
                editedChat = await editChatMutation.mutateAsync(editing);
                setEditing(null);
            }
            const msg = input.trim();
            setInput('');
            const model = models.find(m => m.api_name === editedChat.default_model);
            if (!model) {
                console.error('Model not found');
                return;
            }

            const contents: (TextMessageContent | ImageMessageContent)[] = [];
            if (imageInput) {
                contents.push({type: 'image', content: imageInput.name, image: imageInput, image_type: imageInput.type});
                setImageInput(null);
            }
            contents.push({type: 'text', content: msg});


            if (model.supports_streaming && editedChat.config.tools?.length === 0) {
                setStreamingMessage('');
                await sendMessageStream({role: 'user', contents: contents});
            } else {
                sendMessageMutation.mutate({role: 'user', contents: contents});
            }

            if (chat.messages?.length === 0 || (chat.messages?.length === 1 && chat.messages[0].role === 'system')) {
                refreshSidebar();
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

    const renderMessageContent = (content: MessageContent, index: number) => {
        if (content.type === 'text') {
            return <div key={index}>
                <button className={styles.copyButton} onClick={() => void navigator.clipboard.writeText((content as TextMessageContent).content)}>
                    <FontAwesomeIcon icon={faCopy} />
                </button>
                <Markdown
                    children={(content as TextMessageContent).content.replace(/\\\(/g, '$').replace(/\\\)/g, '$').replace(/\\\[/g, '$$').replace(/\\\]/g, '$$')}
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    className={styles.markdown}
                    key={index}
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
        } else if (content.type === 'image') {
            const imageContent = content as ImageMessageContent;
            return <img key={index} src={(imageContent.image ? URL.createObjectURL(imageContent.image) : undefined) ?? images[imageContent.content]} alt='Image' style={{maxWidth: '100%', maxHeight: '100%'}}/>
        } else if (content.type === 'tool_call') {
            const toolCallContent = content as ToolCallMessageContent;
            if (!(toolCallContent.tool_call_id in toolResultsShown)) {
                setToolResultsShown(tr => (toolCallContent.tool_call_id in tr 
                    ? tr 
                    : {...tr, [toolCallContent.tool_call_id]: false}
                )); 
            }
            let toolResult = undefined;
            for (const message of messages.filter(m => m.role === 'tool')) {
                for (const content of message.contents.filter(c => c.type === 'tool_result')) {
                    if (content.tool_call_id === toolCallContent.tool_call_id) {
                        toolResult = content;
                        break;
                    }
                }
            }
            return <div className={styles.toolCallCtr}>
                <div key={index} className={styles.toolCall}>
                    <h3 className={styles.name}>Tool Call: {toolCallContent.content.name}</h3>
                    <h4 className={styles.argsHeader}>Arguments:</h4>
                    <div className={styles.args}>{Object.entries(toolCallContent.content.args).map((arg, index) => <div key={index} className={styles.arg}>
                        <span className={styles.argName}>{arg[0]}: </span>
                        <span className={styles.argVal}>{arg[1]}</span>
                    </div>)}</div>
                </div>
                {toolResult && 
                <>
                    <button className={styles.showResultButton} onClick={() => setToolResultsShown(tr => ({...tr, [toolCallContent.tool_call_id]: !tr[toolCallContent.tool_call_id]}))}>
                        {toolResultsShown[toolCallContent.tool_call_id] ? 'Hide' : 'Show'} Result
                    </button>
                    <div key={index} className={styles.toolResult + ' ' + (toolResultsShown[toolCallContent.tool_call_id] ? styles.show : '')}>
                        <h3>Result</h3>
                        <pre>{JSON.stringify(toolResult.content, null, 2)}</pre>
                    </div>
                </>
                
                }
            </div>;
        }
    }

    const renderMessage = (message: MessageView, index: number, scroll?: boolean) => {
        if (message.role === 'tool') {
            return null;
        }

        if (message.role === 'system') {
            return <div key={index} className={cx(styles.messageContainer, styles.system)}>
                <button onClick={() => setShowSystem(!showSystem)} className={styles.systemButton}>
                    {showSystem ? 'Hide' : 'Show'} System Prompt
                </button>
                {showSystem && (message.contents[0] as TextMessageContent).content}
            </div>;
        }

        return (
            <div key={index} className={cx(styles.messageContainer, {
                    [styles.user]: message.role === 'user',
                    [styles.assistant]: message.role === 'assistant'
            })} ref={scroll ? scrollToMessage : undefined}>
                
                <div className={cx(styles.info)}>
                        {message.role === 'assistant' && message.model && message.model !== chat?.default_model && <span className={styles.model}>Generated with {models?.find(m => m.api_name === message.model)?.human_name}</span>}
                </div>
                <div className={cx(styles.content)}>
                    {message.role === 'assistant' && <img className={styles.aiLogo} src='/ai-logo.svg' width={50} height={50} alt='AI'/>}
                    <div className={cx(styles.message)}>
                        {message.contents.map(renderMessageContent)}
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
        const model = models?.find(m => m.api_name === (editing ?? chat)?.default_model);
        return <div className={styles.inputContainerCtr}>
            <div className={styles.uploads}>
                {imageInput && <div className={styles.upload}>
                    <img src={URL.createObjectURL(imageInput)} alt='Image' style={{maxWidth: '10%', maxHeight: '10%'}}/>
                    <button onClick={() => setImageInput(null)}>X</button>
                </div>}
            </div>
            <div className={styles.inputContainer}>
                {model && model.supports_images && <label htmlFor='imageInput' className={styles.imageInputLabel} onClick={() => imageInputRef.current?.click()}>
                    <FontAwesomeIcon icon={faImage} />
                    <input
                        type='file'
                        accept='image/*'
                        className={styles.imageInput}
                        ref={imageInputRef}
                        onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            setImageInput(file);
                        }}
                    />
                </label>}
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
            </div>
        </div>;
    }

    if (chatIsLoading || !chat) {
        return <ChatLoading />
    }

    if (chatIsError) {
        return <div>{(chatError as Error)?.message || (chatError as { statusText: string })?.statusText}</div>;
    }

    const messages = chat.messages ?? [];
    console.log(messages);

    if (editing) {
        console.log(editing);
        return <div className={styles.chatContainer}>
            <ChatOptions 
                chat={editing} 
                updateChat={(updateFn) => setEditing(c => c === null ? null : updateFn(c))} // this check is needed for typescript but editing will never actually be null here
                modelsLoading={modelsAreLoading}
                models={models}
                tools={tools}
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
            {streamingMessage && renderMessage({role: 'assistant', contents: [{type: 'text', content: streamingMessage}]}, messages.length)}
            {streamError && <div className={styles.messageContainer}> <div className={styles.message}>Error: {streamError}</div> </div>}
        </div>
        {renderInput()}
      </div>
    );
}