import styles from './App.module.scss';
import { Outlet } from 'react-router-dom';
import Sidebar from './ui/sidebar/sidebar';

function App() {
  
  return (
    <div className={styles.app}>
      <Sidebar userId='c0aba09b-f57e-4998-bee6-86da8b796c5b'/>
      <Outlet />
    </div>
  )
}

export default App
