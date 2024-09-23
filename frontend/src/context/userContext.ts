import { createContext } from "react";
import { User } from "../types";

export interface UserContextType {
    user: User;
    logout: () => void;
    token: string;
}

const UserContext = createContext<UserContextType | null>(null);

export default UserContext;