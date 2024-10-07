import styles from './chat.module.scss';
import { Outlet } from 'react-router-dom';
import Sidebar from '../../ui/sidebar/sidebar';
import { useUser } from '../../hooks';
import { useState } from 'react';

function Chat() {
    const { user } = useUser();

    const [showSidebar, setShowSidebar] = useState<boolean>(true);

    if (!user) {
        return null;
    }

    return (
    <div className={styles.chatPage}>
        <Sidebar show={showSidebar} toggleShow={() => setShowSidebar(!showSidebar)} />
        {!showSidebar && <button className={styles.sidebarToggle} onClick={() => setShowSidebar(true)}>&gt;</button>}
        <Outlet />
    </div>
    )
}

export default Chat;
