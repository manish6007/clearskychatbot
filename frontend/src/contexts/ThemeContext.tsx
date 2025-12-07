/** Theme Context - Provides theme state and toggle functionality */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'dark' | 'light' | 'system';

interface ThemeContextType {
    theme: Theme;
    resolvedTheme: 'dark' | 'light';
    setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<Theme>(() => {
        // Load from localStorage or default to 'dark'
        const saved = localStorage.getItem('clearsky-theme');
        return (saved as Theme) || 'dark';
    });

    const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark');

    useEffect(() => {
        // Save to localStorage
        localStorage.setItem('clearsky-theme', theme);

        // Determine resolved theme
        let resolved: 'dark' | 'light';
        if (theme === 'system') {
            resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        } else {
            resolved = theme;
        }
        setResolvedTheme(resolved);

        // Apply theme class to document
        const root = document.documentElement;
        root.classList.remove('dark', 'light');
        root.classList.add(resolved);

        // Also set data attribute for CSS
        root.setAttribute('data-theme', resolved);
    }, [theme]);

    // Listen for system preference changes
    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        const handleChange = () => {
            if (theme === 'system') {
                setResolvedTheme(mediaQuery.matches ? 'dark' : 'light');
                document.documentElement.classList.remove('dark', 'light');
                document.documentElement.classList.add(mediaQuery.matches ? 'dark' : 'light');
                document.documentElement.setAttribute('data-theme', mediaQuery.matches ? 'dark' : 'light');
            }
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
