import styles from './App.module.scss';
import { Outlet } from 'react-router-dom';
import UserProvider from './context/userContextProvider';

function App() {
  
  return (
    <UserProvider>
      <div className={styles.app}>
        <Outlet />
      </div>
    </UserProvider>
  )
}

export default App;
