/** TopBar component with User dropdown */

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Bell, RefreshCw, Settings, LogOut, ChevronDown } from 'lucide-react';
import { useAppConfig } from '../../hooks';

export function TopBar() {
    const { config, reload } = useAppConfig();
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();

    // Close menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setUserMenuOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <header className="h-16 glass border-b border-surface-700 flex items-center justify-between px-6">
            {/* Left side - Environment indicator */}
            <div className="flex items-center gap-4">
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                    PROD
                </span>
                {config && (
                    <span className="text-sm text-surface-400">
                        v{config.version}
                    </span>
                )}
            </div>

            {/* Right side - Actions */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => reload()}
                    className="p-2 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-700/50 transition-smooth"
                    title="Refresh configuration"
                >
                    <RefreshCw className="h-5 w-5" />
                </button>

                <button className="p-2 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-700/50 transition-smooth relative">
                    <Bell className="h-5 w-5" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-primary-500 rounded-full" />
                </button>

                {/* User dropdown */}
                <div className="relative" ref={menuRef}>
                    <button
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                        className="flex items-center gap-3 pl-4 border-l border-surface-700 hover:bg-surface-700/30 rounded-lg pr-2 py-1 transition-smooth"
                    >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center">
                            <User className="h-4 w-4 text-white" />
                        </div>
                        <div className="text-left hidden sm:block">
                            <span className="text-sm font-medium text-surface-200 block">Manish</span>
                            <span className="text-xs text-surface-400">Admin</span>
                        </div>
                        <ChevronDown className={`h-4 w-4 text-surface-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {/* Dropdown Menu */}
                    {userMenuOpen && (
                        <div className="absolute right-0 top-full mt-2 w-56 py-2 bg-dark-800 border border-surface-600 rounded-xl shadow-xl z-50">
                            {/* User info */}
                            <div className="px-4 py-3 border-b border-surface-700">
                                <p className="text-sm font-medium text-white">Manish Kumar</p>
                                <p className="text-xs text-surface-400">manish@company.com</p>
                            </div>

                            {/* Menu items */}
                            <div className="py-2">
                                <button
                                    onClick={() => {
                                        navigate('/settings');
                                        setUserMenuOpen(false);
                                    }}
                                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-surface-300 hover:bg-surface-700/50 hover:text-white transition-colors"
                                >
                                    <Settings className="h-4 w-4" />
                                    Settings
                                </button>
                            </div>

                            {/* Logout */}
                            <div className="pt-2 border-t border-surface-700">
                                <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors">
                                    <LogOut className="h-4 w-4" />
                                    Sign Out
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}

export default TopBar;
