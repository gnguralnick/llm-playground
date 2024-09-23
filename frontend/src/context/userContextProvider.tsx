import { useCallback, useEffect, useState } from 'react';
import { useGetUser } from '../hooks.ts';
import { User } from '../types.ts';
import { useLocation, useNavigate } from 'react-router-dom';

import UserContext from './userContext.ts';

export default function UserProvider({children}: {children: React.ReactNode}) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const navigate = useNavigate();
    const location = useLocation();

    const { data: userQueryRes, isLoading, isError, error, refetch: getUser } = useGetUser(token ?? undefined);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setToken(null);
        navigate('/login');
    }, [navigate]);

    useEffect(() => {
        if (token && userQueryRes) {
            // if we have a token and a user, set the user
            setUser(userQueryRes);
        }
    }, [token, userQueryRes]);

    useEffect(() => {
        if (!token && location.pathname !== '/login') {
            // if we don't have a token and we're not already on the login page, go to the login page
            navigate('/login');
        }
    }, [token, isLoading, navigate, location]);

    useEffect(() => {
        if (token && !user && !isLoading) {
            // if we have a token but no user, get the user
            void getUser().then(() => navigate('/chat'));
        }
    }, [token, getUser, isLoading, user, navigate]);

    useEffect(() => {
        if (token && isError) {
            // if we have a token and there was an error, log out - token was probably invalid/expired
            logout();
        }
    }, [token, isError, logout]);

    if (!token) {
        return <div>Not logged in</div>;
    }

    if (token && isLoading) {
        return <div>Loading...</div>
    }

    if (isError) {
        console.error(error);
        return <div>{(error as Error)?.message || (error as { statusText?: string })?.statusText}</div>
    }

    if (!user) {
        return <div>No user</div>;
    }

    return (
        <UserContext.Provider value={{user, logout, token}}>
            {children}
        </UserContext.Provider>
    );
}