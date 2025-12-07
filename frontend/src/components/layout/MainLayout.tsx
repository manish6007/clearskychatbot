/** MainLayout component with ClearSky branding */

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface MainLayoutProps {
    children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="flex h-screen overflow-hidden relative">
            {/* Background image with overlay */}
            <div
                className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-5 pointer-events-none z-0"
                style={{
                    backgroundImage: 'url(/clearsky-logo.png)',
                    backgroundSize: '50%',
                    backgroundPosition: 'center center'
                }}
            />
            <div className="absolute inset-0 bg-gradient-to-br from-dark-900/95 via-dark-900/98 to-dark-800/95 pointer-events-none z-0" />

            {/* Content */}
            <div className="relative z-10 flex w-full h-full">
                <Sidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                    <TopBar />
                    <main className="flex-1 overflow-auto p-6">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}

export default MainLayout;
