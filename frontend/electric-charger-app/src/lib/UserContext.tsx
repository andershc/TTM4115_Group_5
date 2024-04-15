"use client"

import { CLIENT } from '@/utils/client';
import { useRouter } from 'next/navigation';
import { createContext, useState } from 'react';

export interface User {
    email: string;
    password: string;
};



export const UserContext = createContext<{
    user: User | null;
    handleLogin: (email: string, password: string) => void;
}>({
    user: null,
    handleLogin: () => null,
});

export const UserProvider = ({ children }: any) => {
    const [user, setUser] = useState<User | null>(null);
    const router = useRouter();

    const handleLogin = async (email: string, password: string) => {
        try {
            // Get URL from environment variable
            const url = `http://localhost:8080/login`
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            })
            if (!response.ok) {
                throw new Error('Login failed')
            }
            const data = await response.json()
            const user = { email: data.email, password: data.password }
            setUser(user)
            console.log(data)
            const payload = {
                command: "login",
                email: user.email
            }
            CLIENT.publish("ttm4115/team_05/command", JSON.stringify(payload));
            CLIENT.subscribe("ttm4115/team_05/charger_status", (error) => {
                if (error) {
                    console.error(error);
                } else {
                    console.log("Subscribed to ttm4115/team_05/charger_status");
                    
                }
            });
            // navigate to chargers page
            router.push('/chargers')
        } catch (error) {
            console.error(error)

        }
    }

    return (
        <UserContext.Provider value={{ user, handleLogin }}>
            {children}
        </UserContext.Provider>
    );
};