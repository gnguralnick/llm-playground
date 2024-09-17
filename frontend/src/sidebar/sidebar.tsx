import {NavLink} from 'react-router-dom';
import styles from './sidebar.module.scss';
import clsx from 'clsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import { Chat } from '../types';


const cx = clsx.bind(styles);

type SidebarProps = {
    userId: string;
};

export default function Sidebar({userId}: SidebarProps) {
    // const router = useRouter();
    // const path = usePathname();
    // const activeChat = path.split('/')[2];

    const handleCreateChat = async () => {
        // const chatId = await createChat(userId);
        // router.push(`/chat/${chatId}`);
    }

    const chats: Chat[] = [];

    return (
        <div className={cx(styles.sidebar)}>
            <button className={styles.createChatButton} onClick={handleCreateChat}>
                <FontAwesomeIcon icon={faPlus} />
            </button>
            <ul className={styles.chatsList}>
                {chats.map((chat) => (
                    <NavLink to={`/chat/${chat.id}`} key={chat.id} className={cx(styles.chat, {
                        [styles.active]: false//chat.id === activeChat
                    })}>
                        <li >
                            {chat.title}
                        </li>
                    </NavLink>
                ))}
            </ul>
        </div>
    );
}

export function SidebarLoading() {
    return (
        <div className={styles.sidebar}>
            <ul className={styles.chatsList}>
                {[1, 2, 3, 4, 5].map((index) => (
                    <li key={index} className={styles.chat}>
                        <div className={styles.loadingChat} />
                    </li>
                ))}
            </ul>
        </div>
    );
}