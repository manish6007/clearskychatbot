/** ChatInput component */

import { useState, KeyboardEvent } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { Button } from '../common';

interface ChatInputProps {
    onSubmit: (question: string) => void;
    loading?: boolean;
    placeholder?: string;
}

export function ChatInput({ onSubmit, loading, placeholder }: ChatInputProps) {
    const [input, setInput] = useState('');

    const handleSubmit = () => {
        if (input.trim() && !loading) {
            onSubmit(input.trim());
            setInput('');
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="glass rounded-xl p-4 border border-surface-600">
            <div className="flex items-end gap-3">
                <div className="flex-1 relative">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder || "Ask a question about your data..."}
                        className="w-full resize-none bg-surface-800/50 rounded-lg px-4 py-3 pr-12 text-surface-100 placeholder-surface-500 border border-surface-600 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-smooth min-h-[48px] max-h-[200px]"
                        rows={1}
                        disabled={loading}
                    />
                    <Sparkles className="absolute right-4 top-1/2 -translate-y-1/2 h-5 w-5 text-primary-400 opacity-50" />
                </div>
                <Button
                    onClick={handleSubmit}
                    loading={loading}
                    disabled={!input.trim() || loading}
                    className="h-12 px-6"
                >
                    <Send className="h-4 w-4 mr-2" />
                    Send
                </Button>
            </div>
            <div className="mt-3 flex items-center gap-4 text-xs text-surface-500">
                <span>Press Enter to send, Shift+Enter for new line</span>
                <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                    Powered by Claude Sonnet
                </span>
            </div>
        </div>
    );
}

export default ChatInput;
