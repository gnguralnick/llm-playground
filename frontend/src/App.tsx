import Chat from "./chat/chat"
import {useState} from 'react';
import { Message } from "./types";
import styles from './App.module.scss';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSendMessage = (message: string) => {
    setMessages([
      ...messages, 
      {role: 'user', content: message},
      {role: 'assistant', content: 'I am a simple assistant, I can only echo what you say.'}
    ]);
  };


  return (
    <div className={styles.app}>
      <Chat messages={messages} onSendMessage={handleSendMessage}/>
    </div>
  )
}

export default App
