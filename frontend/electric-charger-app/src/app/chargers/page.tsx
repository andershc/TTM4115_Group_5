'use client'

import { ChargerInfo } from '@/components/ChargerInfo';
import { UserContext } from '@/lib/UserContext';
import { useRouter } from 'next/navigation';
import { useContext, useState } from 'react';
import { CLIENT } from '../../utils/client.js';

export default function ChargersPage() {
  const { user } = useContext(UserContext);
  const router = useRouter();
  const [chargers, setChargers] = useState([]);
  const [selectedCharger, setSelectedCharger] = useState<Charger | undefined>(undefined);

  CLIENT.on("message", (topic, message) => {
    if(topic !== "ttm4115/team_05/charger_status") return;
    console.log(`Received message ${message}`);
    let chargersFromServer = message.toString();
    // Remove everything before the first '{' character
    const firstBracketIndex = chargersFromServer.indexOf('{');
    chargersFromServer = chargersFromServer.slice(firstBracketIndex);
    console.log(chargersFromServer);
    setChargers(JSON.parse(chargersFromServer.toString()).chargers);
  }
  );

  const handleSelectCharger = (chargerId: string) => {
    // If the user already has a charging session, do not allow selecting another charger
    if((chargers as Charger[]).find((charger: Charger) => charger.startedBy === user?.email)) {
      console.log('User already has a charging session');
      return;
    }
    // Select charger if AVAILABLE
    if((chargers as Charger[]).find((charger: Charger) => charger.id.toString() === chargerId)?.status !== "AVAILABLE") {
      // If the charger is OCCUPIED, but the user is the one who started the charging, navigate to the charger page
      if((chargers as Charger[]).find((charger: Charger) => charger.id.toString() === chargerId)?.startedBy === user?.email) {
        setSelectedCharger((chargers as Charger[]).find((charger: Charger) => charger.id.toString() === chargerId));
        console.log('Navigating to charger page');
      }
      console.log('Charger not available');
      return;
    }
    setSelectedCharger((chargers as Charger[]).find((charger: Charger) => charger.id.toString() === chargerId));
    console.log('Charger selected');
    const payload = {
      command: "select_charger",
      charger: chargerId,
      email: user?.email
    }
    CLIENT.publish("ttm4115/team_05/command", JSON.stringify(payload));
  }


  return (
    <main className="bg-gray-200 text-black flex flex-col items-center gap-2 ">
      <h1>Electric Charger App</h1>
      <p>Hello, {user?.email}!</p>
      <h2>Your charging sessions:</h2>
      <div className="flex flex-row flex-wrap gap-2 items-center justify-center">
      {chargers.filter((charger: Charger) => charger.startedBy === user?.email).map((charger: Charger) => (
        <ChargerInfo key={charger.id} charger={charger} />
      ))}
      </div>
      
      <div className="flex flex-col mt-2 items-center">
        <h2>Chargers</h2>
        <div className="flex flex-col gap-4">
          {chargers.length === 0 ? 
          (<p>No chargers available</p>) :
          (chargers.map((charger: Charger) => (
            <ChargerCard key={charger.name} charger={charger} handleSelectCharger={handleSelectCharger} />
          )))
        }
        </div>
      </div>
    </main>
  );
}

async function fetchChargers() {
  const url = `http://localhost:8080/chargers`
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  })
  if (!response.ok) {
    throw new Error('Fetching chargers failed')
  }
  const data = await response.json()
  console.log(data)
  return data;
}

const ChargerCard = ({ charger, handleSelectCharger }: 
{
  charger: Charger, 
  handleSelectCharger: (chargerId: string) => void
}) => {
  const backGroundColor = charger.status === "AVAILABLE" ? "bg-green-400" : (charger.status === "FAULTY" ? "bg-yellow-400" : "bg-red-400")
  const cursor = charger.status === "AVAILABLE" ? "cursor-pointer" : "cursor-not-allowed"
  const hover = charger.status === "AVAILABLE" ? "hover:bg-green-500" : ""
  return (
    <div onClick={() => handleSelectCharger(charger.id.toString())} className={`flex flex-row gap-2 ${backGroundColor} p-2 rounded ${cursor} ${hover}`}>
      <h3>{charger.name}</h3>
      <p>{charger.status}</p>
    </div>
  );
}

export type Charger = {
  id: number;
  name: string;
  status: string;
  startedBy: string;
  startedAt: string;
};