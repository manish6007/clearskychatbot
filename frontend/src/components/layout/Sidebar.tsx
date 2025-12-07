/** Sidebar component with ClearSky branding */

import { NavLink, useLocation } from 'react-router-dom';
import { MessageSquare, Database, History, Settings } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
    { path: '/', label: 'Ask', icon: MessageSquare },
    { path: '/schema', label: 'Schema Explorer', icon: Database },
    { path: '/history', label: 'History', icon: History },
];

export function Sidebar() {
    const location = useLocation();

    return (
        <aside className="w-64 h-screen flex flex-col glass border-r border-surface-700">
            {/* Logo */}
            <div className="p-4 border-b border-surface-700">
                <div className="flex items-center gap-3">
                    <img
                        src="/clearsky-logo.png"
                        alt="ClearSky"
                        className="h-10 w-10 rounded-lg object-cover"
                    />
                    <div>
                        <h1 className="text-lg font-bold gradient-text">ClearSky</h1>
                        <p className="text-xs text-surface-400">Text-to-SQL Assistant</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    const Icon = item.icon;

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={clsx(
                                'flex items-center gap-3 px-4 py-3 rounded-lg transition-smooth',
                                isActive
                                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                    : 'text-surface-300 hover:bg-surface-700/50 hover:text-surface-100'
                            )}
                        >
                            <Icon className="h-5 w-5" />
                            <span className="font-medium">{item.label}</span>
                        </NavLink>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-surface-700">
                <NavLink
                    to="/settings"
                    className={({ isActive }) =>
                        `flex items-center gap-3 px-4 py-2 w-full rounded-lg transition-smooth ${isActive
                            ? 'bg-primary-500/20 text-primary-400'
                            : 'text-surface-400 hover:bg-surface-700/50 hover:text-surface-100'
                        }`
                    }
                >
                    <Settings className="h-5 w-5" />
                    <span className="text-sm">Settings</span>
                </NavLink>
            </div>
        </aside>
    );
}

export default Sidebar;
