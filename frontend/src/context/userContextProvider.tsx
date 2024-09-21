import { useCallback, useEffect, useState } from 'react';
import { backendFetch, useGetUser } from '../hooks.ts';
import { User } from '../types.ts';
import { useLocation, useNavigate } from 'react-router-dom';

import UserContext from './userContext.ts';

export default function UserProvider({children}: {children: React.ReactNode}) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const navigate = useNavigate();
    const location = useLocation();

    const { data: userQueryRes, isLoading, isError, error, refetch: getUser } = useGetUser(token ?? undefined);

    const login = async (loginForm: FormData) => {
        console.log('logging in');
        const response = await backendFetch('/token', {
            method: 'POST',
            body: loginForm,
        });
        const json = (await response.json()) as {access_token: string};
        const token: string = json.access_token;
        localStorage
            .setItem('token', token);
        setToken(token);
    }

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setToken(null);
        navigate('/login');
    }, [navigate]);

    useEffect(() => {
        if (token && userQueryRes) {
            setUser(userQueryRes);
        }
    }, [token, userQueryRes, navigate]);

    useEffect(() => {
        if (!token && location.pathname !== '/login') {
            navigate('/login');
        }
    }, [token, isLoading, navigate, location]);

    useEffect(() => {
        if (token && !user && !isLoading) {
            void getUser().then(() => navigate('/chat'));
        }
    }, [token, getUser, isLoading, user, navigate]);

    useEffect(() => {
        if (token && isError) {
            logout();
        }
    }, [token, isError, logout]);

    console.log('token', token);
    console.log('user', user);

    if (token && isLoading) {
        return <div>Loading...</div>
    }

    if (isError) {
        console.error(error);
        return <div>{(error as Error)?.message || (error as { statusText?: string })?.statusText}</div>
    }

    return (
        <UserContext.Provider value={{user, login, logout, token}}>
            {children}
        </UserContext.Provider>
    );
}