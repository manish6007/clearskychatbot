/** SettingsPage - Application settings and configuration */

import { useState } from 'react';
import { Card, Button } from '../components/common';
import { useTheme } from '../contexts';
import {
    Settings, Database, Palette, Bell, Shield,
    ChevronRight, Moon, Sun, Monitor, Save, RefreshCw, Check
} from 'lucide-react';

interface SettingSection {
    id: string;
    title: string;
    icon: React.ReactNode;
    description: string;
}

const settingSections: SettingSection[] = [
    { id: 'general', title: 'General', icon: <Settings className="h-5 w-5" />, description: 'App preferences and defaults' },
    { id: 'database', title: 'Database', icon: <Database className="h-5 w-5" />, description: 'Athena connection settings' },
    { id: 'appearance', title: 'Appearance', icon: <Palette className="h-5 w-5" />, description: 'Theme and display options' },
    { id: 'notifications', title: 'Notifications', icon: <Bell className="h-5 w-5" />, description: 'Alert preferences' },
    { id: 'security', title: 'Security', icon: <Shield className="h-5 w-5" />, description: 'Access and permissions' },
];

export function SettingsPage() {
    const [activeSection, setActiveSection] = useState('general');
    const { theme, setTheme, resolvedTheme } = useTheme();
    const [maxRows, setMaxRows] = useState(1000);
    const [enableCharts, setEnableCharts] = useState(true);
    const [enableDebug, setEnableDebug] = useState(true);
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const renderSectionContent = () => {
        switch (activeSection) {
            case 'general':
                return (
                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-surface-200 mb-2">
                                Default Max Rows
                            </label>
                            <input
                                type="number"
                                value={maxRows}
                                onChange={(e) => setMaxRows(Number(e.target.value))}
                                className="w-full px-4 py-2 bg-dark-700 border border-surface-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                            />
                            <p className="text-xs text-surface-400 mt-1">
                                Maximum rows returned per query
                            </p>
                        </div>

                        <div className="flex items-center justify-between">
                            <div>
                                <label className="block text-sm font-medium text-surface-200">
                                    Enable Charts
                                </label>
                                <p className="text-xs text-surface-400">
                                    Show visualizations for query results
                                </p>
                            </div>
                            <button
                                onClick={() => setEnableCharts(!enableCharts)}
                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${enableCharts ? 'bg-primary-500' : 'bg-dark-600'
                                    }`}
                            >
                                <span
                                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${enableCharts ? 'translate-x-6' : 'translate-x-1'
                                        }`}
                                />
                            </button>
                        </div>

                        <div className="flex items-center justify-between">
                            <div>
                                <label className="block text-sm font-medium text-surface-200">
                                    Debug Mode
                                </label>
                                <p className="text-xs text-surface-400">
                                    Show detailed agent thinking steps
                                </p>
                            </div>
                            <button
                                onClick={() => setEnableDebug(!enableDebug)}
                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${enableDebug ? 'bg-primary-500' : 'bg-dark-600'
                                    }`}
                            >
                                <span
                                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${enableDebug ? 'translate-x-6' : 'translate-x-1'
                                        }`}
                                />
                            </button>
                        </div>
                    </div>
                );

            case 'database':
                return (
                    <div className="space-y-6">
                        <div className="p-4 bg-dark-700/50 rounded-lg border border-surface-600">
                            <h4 className="text-sm font-medium text-surface-200 mb-3">Connection Status</h4>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                                <span className="text-green-400 text-sm">Connected to AWS Athena</span>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-surface-200 mb-2">
                                Database
                            </label>
                            <input
                                type="text"
                                value="athena_db"
                                readOnly
                                className="w-full px-4 py-2 bg-dark-800 border border-surface-700 rounded-lg text-surface-400 cursor-not-allowed"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-surface-200 mb-2">
                                Workgroup
                            </label>
                            <input
                                type="text"
                                value="primary"
                                readOnly
                                className="w-full px-4 py-2 bg-dark-800 border border-surface-700 rounded-lg text-surface-400 cursor-not-allowed"
                            />
                        </div>

                        <Button variant="secondary" className="flex items-center gap-2">
                            <RefreshCw className="h-4 w-4" />
                            Test Connection
                        </Button>
                    </div>
                );

            case 'appearance':
                return (
                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-surface-200 mb-3">
                                Theme
                            </label>
                            <p className="text-xs text-surface-400 mb-4">
                                Current: <span className="text-primary-400 font-medium">{resolvedTheme}</span>
                            </p>
                            <div className="grid grid-cols-3 gap-3">
                                {[
                                    { id: 'dark', label: 'Dark', icon: Moon },
                                    { id: 'light', label: 'Light', icon: Sun },
                                    { id: 'system', label: 'System', icon: Monitor },
                                ].map((option) => {
                                    const Icon = option.icon;
                                    const isActive = theme === option.id;
                                    return (
                                        <button
                                            key={option.id}
                                            onClick={() => setTheme(option.id as 'dark' | 'light' | 'system')}
                                            className={`relative flex flex-col items-center gap-2 p-4 rounded-lg border transition-all ${isActive
                                                    ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                                                    : 'border-surface-600 bg-dark-700 text-surface-300 hover:border-surface-500'
                                                }`}
                                        >
                                            {isActive && (
                                                <div className="absolute top-2 right-2">
                                                    <Check className="h-4 w-4 text-primary-400" />
                                                </div>
                                            )}
                                            <Icon className="h-6 w-6" />
                                            <span className="text-sm">{option.label}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-surface-200 mb-2">
                                Accent Color
                            </label>
                            <div className="flex gap-3">
                                {['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899'].map((color) => (
                                    <button
                                        key={color}
                                        className="w-8 h-8 rounded-full border-2 border-white/20 hover:border-white/50 transition-colors hover:scale-110"
                                        style={{ backgroundColor: color }}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>
                );

            case 'notifications':
                return (
                    <div className="space-y-4">
                        {[
                            { id: 'query_complete', label: 'Query Complete', description: 'When a query finishes executing' },
                            { id: 'errors', label: 'Errors', description: 'When queries fail or errors occur' },
                            { id: 'tips', label: 'Tips & Suggestions', description: 'Helpful tips for using ClearSky' },
                        ].map((item) => (
                            <div key={item.id} className="flex items-center justify-between p-4 bg-dark-700/50 rounded-lg">
                                <div>
                                    <label className="block text-sm font-medium text-surface-200">
                                        {item.label}
                                    </label>
                                    <p className="text-xs text-surface-400">{item.description}</p>
                                </div>
                                <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-500">
                                    <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-6" />
                                </button>
                            </div>
                        ))}
                    </div>
                );

            case 'security':
                return (
                    <div className="space-y-6">
                        <div className="p-4 bg-dark-700/50 rounded-lg border border-surface-600">
                            <h4 className="text-sm font-medium text-surface-200 mb-2">AWS Authentication</h4>
                            <p className="text-xs text-surface-400 mb-3">
                                Using IAM credentials from environment
                            </p>
                            <div className="flex items-center gap-2 text-green-400 text-sm">
                                <Shield className="h-4 w-4" />
                                <span>Authenticated</span>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-surface-200 mb-2">
                                Session Timeout
                            </label>
                            <select className="w-full px-4 py-2 bg-dark-700 border border-surface-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500">
                                <option>30 minutes</option>
                                <option>1 hour</option>
                                <option>4 hours</option>
                                <option>Never</option>
                            </select>
                        </div>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-white">Settings</h1>
                <p className="text-surface-400 mt-1">Manage your ClearSky preferences</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Settings Navigation */}
                <Card className="p-2 h-fit">
                    <nav className="space-y-1">
                        {settingSections.map((section) => (
                            <button
                                key={section.id}
                                onClick={() => setActiveSection(section.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeSection === section.id
                                        ? 'bg-primary-500/20 text-primary-400'
                                        : 'text-surface-300 hover:bg-surface-700/50'
                                    }`}
                            >
                                {section.icon}
                                <span className="flex-1 text-left text-sm font-medium">{section.title}</span>
                                <ChevronRight className={`h-4 w-4 transition-transform ${activeSection === section.id ? 'rotate-90' : ''
                                    }`} />
                            </button>
                        ))}
                    </nav>
                </Card>

                {/* Settings Content */}
                <Card className="md:col-span-2 p-6">
                    <div className="mb-6">
                        <h2 className="text-lg font-semibold text-white">
                            {settingSections.find(s => s.id === activeSection)?.title}
                        </h2>
                        <p className="text-sm text-surface-400">
                            {settingSections.find(s => s.id === activeSection)?.description}
                        </p>
                    </div>

                    {renderSectionContent()}

                    <div className="mt-8 pt-6 border-t border-surface-700 flex justify-end gap-3">
                        <Button variant="secondary">Cancel</Button>
                        <Button onClick={handleSave} className="flex items-center gap-2">
                            {saved ? (
                                <>
                                    <Check className="h-4 w-4" />
                                    Saved!
                                </>
                            ) : (
                                <>
                                    <Save className="h-4 w-4" />
                                    Save Changes
                                </>
                            )}
                        </Button>
                    </div>
                </Card>
            </div>
        </div>
    );
}

export default SettingsPage;
