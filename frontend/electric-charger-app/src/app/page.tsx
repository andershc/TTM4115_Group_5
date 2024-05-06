'use client'

import { UserContext } from "@/lib/UserContext";
import { useContext, useState } from "react";

export default function Home() {
  const [email, setEmail] = useState<string>('')
  const [password, setPassword] = useState<string>('')

  const { handleLogin } = useContext(UserContext);

  return (
    <main className="flex flex-col bg-gray-200 items-center text-black">
      <h1 className="text-xl font-bold">Electric Charger App</h1>
      {/* Login Component */}
      <div className="flex flex-col gap-10 w-full items-center text-black pt-10">
        <label className="flex flex-col">
          <span>Email</span>
          <input type="email"  onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="flex flex-col">
          <span>Password</span>
          <input type="password" onChange={(p) => setPassword(p.target.value)} />
        </label>
        <button className="bg-lime-400 text-black p-2 rounded" onClick={() => handleLogin(email, password)}>Login</button>
      </div>
    </main>
  );
}
