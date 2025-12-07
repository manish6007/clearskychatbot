/** QuestionContext - Provides sample question submission across components */

import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';

interface QuestionContextType {
    pendingQuestion: string | null;
    submitQuestion: (question: string) => void;
    clearPendingQuestion: () => void;
}

const QuestionContext = createContext<QuestionContextType | undefined>(undefined);

export function QuestionProvider({ children }: { children: ReactNode }) {
    const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);

    const submitQuestion = useCallback((question: string) => {
        setPendingQuestion(question);
    }, []);

    const clearPendingQuestion = useCallback(() => {
        setPendingQuestion(null);
    }, []);

    return (
        <QuestionContext.Provider value={{ pendingQuestion, submitQuestion, clearPendingQuestion }}>
            {children}
        </QuestionContext.Provider>
    );
}

export function useQuestion() {
    const context = useContext(QuestionContext);
    if (context === undefined) {
        throw new Error('useQuestion must be used within a QuestionProvider');
    }
    return context;
}
