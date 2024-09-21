import { createContext } from "react";
import { User } from "../types";

export interface UserContextType {
    user: User | null;
    login: (loginForm: FormData) => Promise<void>;
    logout: () => void;
    token: string | null;
}

const UserContext = createContext<UserContextType | null>(null);

export default UserContext;