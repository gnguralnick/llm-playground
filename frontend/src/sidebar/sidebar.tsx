import {NavLink, useParams, useNavigate} from 'react-router-dom';
import styles from './sidebar.module.scss';
import clsx from 'clsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import { Chat } from '../types';
import { useQuery, useMutation, useQueryClient } from 'react-query';


const cx = clsx.bind(styles);

type SidebarProps = {
    userId: string;
};

function SidebarLoading() {
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

export default function Sidebar({userId}: SidebarProps) {

    const { chatId } = useParams();
    const queryClient = useQueryClient();
    const navigate = useNavigate();

    const { isLoading, isError, error, data } = useQuery({
        queryKey: userId,
        queryFn: async () => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/`);
            return response.json();
        }
    });

    const mutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: 'New Chat'})
            });
            return response.json();
        },
        onSuccess: (data: Chat) => {
            queryClient.invalidateQueries(userId);
            navigate(`/chat/${data.id}`);
        }
    });

    if (isLoading) {
        return <SidebarLoading />;
    }

    if (isError) {
        return <div>{(error as Error)?.message || (error as { statusText: string })?.statusText}</div>;
    }

    const chats = data as Chat[];

    return (
        <div className={cx(styles.sidebar)}>
            <button className={styles.createChatButton} onClick={() => mutation.mutate()}>
                <FontAwesomeIcon icon={faPlus} />
            </button>
            <ul className={styles.chatsList}>
                {chats.map((chat) => (
                    <NavLink to={`/chat/${chat.id}`} key={chat.id} className={cx(styles.chat, {
                        [styles.active]: chat.id === chatId
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

