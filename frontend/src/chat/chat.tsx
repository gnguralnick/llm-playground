import { useState } from 'react';
import styles from './chat.module.scss';
import clsx from 'clsx';
import { ArrowUp } from '../assets/icons';
import { Message } from '../types';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Chat as ChatType } from '../types';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
    
    const { chatId } = useParams();
    const queryClient = useQueryClient();

    const {isLoading, isError, error, data } = useQuery({
        queryKey: chatId,
        queryFn: async () => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/${chatId}`);
            return (await response.json()) as ChatType;
        }
    });

    const mutation = useMutation({
        mutationFn: async (msg: Pick<Message, "content" | "role"> & Partial<Message>) => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/${chatId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(msg)
            });
            return (await response.json()) as Message;
        },
        onSuccess: () => {
            void queryClient.invalidateQueries(chatId);
        }
    });

    const handleSend = () => {
        if (input.trim() !== '') {
            mutation.mutate({
                role: 'user',
                content: input
            });
            setInput('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    const renderMessage = (message: {role: string, content: string}, index: number) => {
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
            })}>
                {message.role === 'assistant' && <img className={styles.aiLogo} src='/ai-logo.svg' width={50} height={50} alt='AI'/>}
                <div className={cx(styles.message)}>
                    <Markdown
                        children={message.content}
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                        className={styles.markdown}
                        components={{
                        code(props) {
                            const {children, className, node, ...rest} = props
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
                        }}
                    />
                </div>
            </div>
        );
    };

    if (isLoading || !data) {
        return <ChatLoading />
    }

    if (isError) {
        return <div>{(error as Error)?.message || (error as { statusText: string })?.statusText}</div>;
    }

    const chat = data;
    const messages = chat.messages ?? [];

  
    return (
      <div className={styles.chatContainer}>
        <div className={styles.messagesContainer}>
            {messages.length > 0 && messages.map(renderMessage)}
        </div>
        <div className={styles.inputContainer}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className={styles.input}
            placeholder="Type a message..."
          />
          <button onClick={handleSend} className={styles.button}>
            <ArrowUp />
          </button>
        </div>
      </div>
    );
}