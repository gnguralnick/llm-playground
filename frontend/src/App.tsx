import styles from './App.module.scss';
import { Outlet, useNavigate } from 'react-router-dom';
import UserProvider from './context/userContextProvider';
import { useEffect } from 'react';

function App() {

  const navigate = useNavigate();

  useEffect(() => {
    navigate('/chat');
  }, [navigate]);
  
  return (
    <UserProvider>
      <div className={styles.app}>
        <Outlet />
      </div>
    </UserProvider>
  )
}

export default App;
