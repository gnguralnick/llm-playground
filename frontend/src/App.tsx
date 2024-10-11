import styles from './App.module.scss';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import UserProvider from './context/userContextProvider';
import { useEffect } from 'react';

function App() {

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.pathname === '/') {
      navigate('/chat');
    }
  }, [navigate, location.pathname]);
  
  return (
    <UserProvider>
      <div className={styles.app}>
        <Outlet />
      </div>
    </UserProvider>
  )
}

export default App;
