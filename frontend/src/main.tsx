import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import Error from './error.tsx';
import './index.scss';

import {
  createBrowserRouter,
  RouterProvider,
} from 'react-router-dom';

import { QueryClient, QueryClientProvider } from 'react-query';

import ChatPage from './pages/chat/chat.tsx';
import Chat from './ui/chat/chat.tsx';
import Login from './pages/login/login.tsx';
import User from './pages/user/user.tsx';
import Signup from './pages/signup/signup.tsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    errorElement: <Error />,
    children: [
      {
        path: '/chat/',
        element: <ChatPage />,
        children: [
          {
            path: '/chat/:chatId',
            element: <Chat />,
            
          },
        ]
      },
      {
        path: '/user/',
        element: <User />
      }
    ]
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/signup',
    element: <Signup />,
  }
]);

const queryClient = new QueryClient();



createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router}/>
    </QueryClientProvider>
  </StrictMode>,
);
