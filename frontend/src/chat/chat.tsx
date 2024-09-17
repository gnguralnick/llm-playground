import { useState } from 'react';
import styles from './chat.module.scss';
import clsx from 'clsx';
import { ArrowUp } from '../assets/icons';
import { Message } from '../types';



const cx = clsx.bind(styles);

export default function Chat() {
    const [input, setInput] = useState('');

    const [messages, setMessages] = useState<Message[]>([]);

    const handleSend = () => {
        if (input.trim() !== '') {
            setMessages([
                ...messages, 
                {role: 'user', content: input},
                {role: 'assistant', content: 'I am a simple assistant, I can only echo what you say.'}
            ]);
            setInput('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    const renderMessage = (message: {role: string, content: string}, index: number) => {
        if (message.role !== 'user' && message.role !== 'assistant') {
            return null;
        }

        return (
            <div key={index} className={cx(styles.messageContainer, {
                    [styles.user]: message.role === 'user',
                    [styles.assistant]: message.role === 'assistant'
            })}>
                {message.role === 'assistant' && <img className={styles.aiLogo} src='/ai-logo.svg' width={50} height={50} alt='AI'/>}
                <div className={cx(styles.message)}>
                    {message.content}
                </div>
            </div>
        );
    };
  
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