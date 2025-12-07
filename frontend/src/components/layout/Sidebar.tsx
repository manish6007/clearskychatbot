/** Sidebar component with ClearSky branding and sample questions */

import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { MessageSquare, Database, History, Settings, Lightbulb, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';
import { useQuestion } from '../../contexts';

const navItems = [
    { path: '/', label: 'Ask', icon: MessageSquare },
    { path: '/schema', label: 'Schema Explorer', icon: Database },
    { path: '/history', label: 'History', icon: History },
];

const sampleQuestions = [
    "Show all customers",
    "Total revenue by product",
    "Orders from last month",
    "Top 10 customers by spend",
    "Low stock products",
];

export function Sidebar() {
    const location = useLocation();
    const navigate = useNavigate();
    const { submitQuestion } = useQuestion();
    const [samplesOpen, setSamplesOpen] = useState(true);

    const handleQuestionClick = (question: string) => {
        // Navigate to chat if not already there
        if (location.pathname !== '/') {
            navigate('/');
        }
        // Trigger the question via context
        submitQuestion(question);
    };

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
            <nav className="p-4 space-y-2">
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

            {/* Sample Questions */}
            <div className="px-4 flex-1">
                <button
                    onClick={() => setSamplesOpen(!samplesOpen)}
                    className="flex items-center justify-between w-full py-2 text-xs font-medium text-surface-400 uppercase tracking-wide hover:text-surface-300 transition-colors"
                >
                    <span className="flex items-center gap-2">
                        <Lightbulb className="h-3.5 w-3.5" />
                        Sample Questions
                    </span>
                    {samplesOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {samplesOpen && (
                    <div className="space-y-1.5 mt-2">
                        {sampleQuestions.map((question, i) => (
                            <button
                                key={i}
                                onClick={() => handleQuestionClick(question)}
                                className="w-full text-left text-xs px-3 py-2 rounded-lg bg-surface-800/30 text-surface-400 hover:bg-primary-500/10 hover:text-primary-400 transition-smooth border border-transparent hover:border-primary-500/20"
                            >
                                "{question}"
                            </button>
                        ))}
                    </div>
                )}
            </div>

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
