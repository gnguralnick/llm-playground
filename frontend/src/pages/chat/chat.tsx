import styles from './chat.module.scss';
import { Outlet } from 'react-router-dom';
import Sidebar from '../../ui/sidebar/sidebar';
import { useUser } from '../../hooks';

function Chat() {
    const { user } = useUser();

    if (!user) {
        return null;
    }

    return (
    <div className={styles.chatPage}>
        <Sidebar userId={user?.id} />
        <Outlet />
    </div>
    )
}

export default Chat;
