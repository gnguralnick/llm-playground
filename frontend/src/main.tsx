import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import Error from './error.tsx';
import './index.scss';

import {
  createBrowserRouter,
  RouterProvider,
} from 'react-router-dom';
import Chat from './chat/chat.tsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    errorElement: <Error />,
    children: [
      {
        path: '/chat/:chatId',
        element: <Chat />,
      }
    ]
  }
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
