'use client'

import { ChargerInfo } from "@/components/ChargerInfo";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Charger } from "../page";

export default function ChargerPage() {
    const chargerId = useParams().chargerId;

    //Fecth charger data from server
    const [charger, setCharger] = useState<Charger | undefined>(undefined);

    useEffect(() => {
        // Fetch charger data from server
        fetchCharger(chargerId).then(charger => {
            setCharger(charger);
        }).catch(error => {
            console.error('Error in fetching charger:', error);
            setCharger(undefined);
        });
    }, [chargerId]);

    return (
        <main className="bg-gray-200 text-black flex flex-col items-center">
            <h1>Electric Charger App</h1>
            {charger ? <ChargerInfo charger={charger} /> : <p>Loading...</p>}
        </main>
    );
}

async function fetchCharger(chargerId: any) {
    try {
        const response = await fetch(`http://localhost:8080/charger?id=${encodeURIComponent(chargerId)}`);
        if (!response.ok) {
            // Handle HTTP errors e.g., 404, 500 etc.
            throw new Error('Failed to fetch charger: ' + response.statusText);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching charger:', error);
        // Handle errors like network issues, bad JSON, etc.
        // Optionally, return a default value or error indicator
    }
}

