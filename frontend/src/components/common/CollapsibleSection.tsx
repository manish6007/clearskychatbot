/** CollapsibleSection component */

import { useState, ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface CollapsibleSectionProps {
    title: string;
    children: ReactNode;
    defaultOpen?: boolean;
    className?: string;
}

export function CollapsibleSection({
    title,
    children,
    defaultOpen = false,
    className,
}: CollapsibleSectionProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className={clsx('border border-surface-700 rounded-lg overflow-hidden', className)}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-4 py-3 bg-surface-800/50 hover:bg-surface-700/50 transition-colors text-left"
            >
                <span className="font-medium text-surface-200">{title}</span>
                {isOpen ? (
                    <ChevronDown className="h-5 w-5 text-surface-400" />
                ) : (
                    <ChevronRight className="h-5 w-5 text-surface-400" />
                )}
            </button>
            {isOpen && (
                <div className="p-4 bg-surface-900/30 animate-fade-in">
                    {children}
                </div>
            )}
        </div>
    );
}

export default CollapsibleSection;
