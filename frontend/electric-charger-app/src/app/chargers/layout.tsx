'use client'

import { UserContext } from "@/lib/UserContext";
import { ReactNode, useContext, useEffect } from "react";

export default function Layout({ children }: {
    children: ReactNode;
}) {
    const { user } = useContext(UserContext);

    useEffect(() => {
        if (!user) {
            // redirect to login page
            console.log('User not logged in');
            window.location.href = '/';
        }
    }
    , [user]);


    return (
        <html lang="en" className="bg-gray-200">
                <body>{children}</body>
        </html>
    );
}