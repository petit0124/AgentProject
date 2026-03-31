"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import { chatWithBot, getHistory } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

type Message = {
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
};

export default function ChatComponent() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await chatWithBot(userMessage.content);
            const botMessage: Message = {
                role: 'assistant',
                content: response.answer,
                sources: response.sources
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error(error);
            const errorMessage: Message = { role: 'assistant', content: "抱歉，遇到了一些问题，请稍后再试。" };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-[600px] w-full max-w-2xl mx-auto bg-white/50 backdrop-blur-md rounded-2xl border border-gray-100 shadow-xl overflow-hidden">
            <div className="bg-white/80 p-4 border-b border-gray-100 flex items-center gap-2">
                <Bot className="w-5 h-5 text-blue-600" />
                <h2 className="font-bold text-gray-800">智能助手</h2>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-2">
                        <Bot className="w-12 h-12 opacity-20" />
                        <p className="text-sm">上传文档后，开始提问吧！</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={cn(
                            "flex w-full",
                            msg.role === 'user' ? "justify-end" : "justify-start"
                        )}
                    >
                        <div className={cn(
                            "flex max-w-[80%] gap-3",
                            msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                        )}>
                            <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm",
                                msg.role === 'user' ? "bg-blue-600 text-white" : "bg-white text-blue-600 border border-gray-100"
                            )}>
                                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                            </div>

                            <div className={cn(
                                "p-3 rounded-2xl text-sm leading-relaxed shadow-sm",
                                msg.role === 'user'
                                    ? "bg-blue-600 text-white rounded-tr-none"
                                    : "bg-white text-gray-700 border border-gray-100 rounded-tl-none"
                            )}>
                                <p>{msg.content}</p>
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-2 pt-2 border-t border-gray-100/50 text-xs opacity-70">
                                        <p className="font-semibold mb-1">参考来源:</p>
                                        <ul className="list-disc list-inside">
                                            {msg.sources.map((source, i) => (
                                                <li key={i} className="truncate max-w-[200px]">{source}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                ))}
                {loading && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex w-full justify-start"
                    >
                        <div className="flex max-w-[80%] gap-3 flex-row">
                            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm bg-white text-blue-600 border border-gray-100">
                                <Bot className="w-4 h-4" />
                            </div>
                            <div className="p-3 rounded-2xl bg-white text-gray-700 border border-gray-100 rounded-tl-none shadow-sm flex items-center">
                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                <span className="text-sm">思考中...</span>
                            </div>
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 bg-white/80 border-t border-gray-100">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="输入您的问题..."
                        className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-inner"
                        disabled={loading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || loading}
                        className="absolute right-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors shadow-md"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
