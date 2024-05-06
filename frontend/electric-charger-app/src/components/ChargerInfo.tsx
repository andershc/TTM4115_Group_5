'use client'

import { Charger } from '@/app/chargers/page';
import { UserContext } from '@/lib/UserContext';
import { CLIENT } from '@/utils/client';
import React, { useContext, useEffect, useState } from 'react';


type ChargerInfoProps = {
  charger: Charger;
};

const ChargerInfo: React.FC<ChargerInfoProps> = ({ charger }) => {
    const [isPaymentModalOpen, setPaymentModalOpen] = useState(false);

    const { user } = useContext(UserContext);

    const openModal = () => setPaymentModalOpen(true);
    const closeModal = () => setPaymentModalOpen(false);

    const [progress, setProgress] = useState(0);

    useEffect(() => {
        if (charger.status !== "CHARGING") return undefined;
    
        const startTime = new Date(charger.startedAt).getTime();
        const interval = setInterval(() => {
          const currentTime = new Date().getTime();
          const elapsedMs = currentTime - startTime;
          setProgress(Math.min(100, Math.max(0, (elapsedMs / charger.totalChargingTime) * 100)));
        }, 1000);
    
        return () => clearInterval(interval);
      }, [charger.status , charger.startedAt, charger.totalChargingTime]);

    const handleDisconnectCharger = (chargerId: number) => {
        const payload = {
            command: "disconnect_charger",
            charger: chargerId,
            email: user?.email ?? ''
        }
        CLIENT.publish('ttm4115/team_05/command', JSON.stringify(payload));
        console.log(`Disconnecting charger ${chargerId}`);
    }


    return (
        <div className="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden md:max-w-2xl">
            <div className="md:flex">
                <div className="p-8">
                    <div className="uppercase tracking-wide text-sm text-indigo-500 font-semibold">{charger.id}</div>
                    <a href="#" className="block mt-1 text-lg leading-tight font-medium text-black hover:underline">{charger.name}</a>
                    <p className="mt-2 text-gray-500">Status: {charger.status}</p>
                    {charger.startedAt != null && charger.startedAt !== "" && <p className="mt-2 text-gray-500">Started at: {charger.startedAt}</p>}
                    {charger.status !== "CHARGING" ? (
                        <div className='flex flex-col gap-2'>
                            <div className='flex flex-row gap-2'>
                                
                                <button
                                    className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                                    onClick={openModal}
                                >
                                    Start Charging
                                </button>
                                <button className='
                                    mt-4 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded'
                                    onClick={() => handleDisconnectCharger(charger.id)}
                                >
                                    Disconnect Charger
                                </button>
                                
                            </div>
                            {charger.totalChargingTime === 0 && charger.startedAt === null && (
                                    <p className='text-red-600'>Cable not connected. Please plug in the charger to your car</p>
                                )}
                        </div>
                        ) : (
                        <div className='flex flex-row items-center gap-2'>
                            <img src="/ios-battery-charging.png" width={18}/>
                            <div className="w-full bg-gray-200 rounded h-2.5">
                                <div className="bg-blue-600 h-2.5 rounded" style={{ width: `${progress}%` }}></div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            {isPaymentModalOpen && (
                <PaymentModal closeModal={closeModal} handleStartCharging={handleStartCharging} chargerId={charger.id} />
            )}
            
        </div>
    );
};

const PaymentModal = ({ closeModal, handleStartCharging, chargerId }: { closeModal: () => void,
    handleStartCharging: (chargerId: number, email: string) => void, chargerId: number
}) => {
    const { user } = useContext(UserContext);

    console.log(user)

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
            <div className="bg-white p-4 rounded-lg shadow-lg text-center">
                <h3 className="text-lg font-bold">Confirm Payment</h3>
                <p className="text-gray-600">Do you want to start the charging process?</p>
                <div className="mt-4">
                    <button
                        className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mr-2"
                        onClick={() => {
                            console.log("Payment confirmed");
                            handleStartCharging(chargerId, user?.email ?? '');
                            closeModal();
                        }}
                    >
                        Confirm
                    </button>
                    <button
                        className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
                        onClick={closeModal}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export { ChargerInfo };

function handleStartCharging(chargerId: number, email: string) {
    if (!email || email === '') {
        console.error('User not logged in');
        return;
    }
    const payload = {
        command : 'pay',
        charger: chargerId,
        email: email
    }
    CLIENT.publish('ttm4115/team_05/command', JSON.stringify(payload));
    console.log(`Starting charging for charger ${chargerId}`);
}
