"use client";

import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export default function UploadComponent() {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');
    const [chunksContent, setChunksContent] = useState<string[]>([]);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
            setStatus('idle');
            setChunksContent([]);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus('idle');
            setChunksContent([]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setStatus('idle');
        setChunksContent([]);
        try {
            const result = await uploadDocument(file);
            setStatus('success');
            setMessage(`文档上传并处理成功！共生成 ${result.chunks} 个分块。`);
            if (result.chunk_content && Array.isArray(result.chunk_content)) {
                setChunksContent(result.chunk_content);
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
            setMessage('上传失败，请重试。');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="w-full max-w-md mx-auto p-6 bg-white/50 backdrop-blur-md rounded-2xl border border-gray-100 shadow-xl transition-all hover:shadow-2xl">
            <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-600" />
                文档上传
            </h2>

            <div
                className={cn(
                    "relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer overflow-hidden group",
                    isDragging ? "border-blue-500 bg-blue-50/50 scale-[1.02]" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50",
                    status === 'error' && "border-red-300 bg-red-50/20"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-upload')?.click()}
            >
                <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    onChange={handleFileChange}
                    accept=".pdf,.docx,.ppt,.pptx,.xlsx,.xls,.txt,.md"
                />

                <div className="flex flex-col items-center gap-3">
                    <div className={cn(
                        "w-12 h-12 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 transition-transform duration-300 group-hover:scale-110",
                        file && "bg-green-100 text-green-600"
                    )}>
                        {file ? <FileText className="w-6 h-6" /> : <Upload className="w-6 h-6" />}
                    </div>

                    <div className="space-y-1">
                        <p className="text-sm font-medium text-gray-700">
                            {file ? file.name : "点击或拖拽文件到这里"}
                        </p>
                        {!file && (
                            <p className="text-xs text-gray-400">
                                支持 PDF, Word, PPT, Excel, TXT, MD
                            </p>
                        )}
                    </div>
                </div>
            </div>

            <AnimatePresence>
                {message && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={cn(
                            "mt-4 p-3 rounded-lg text-sm flex items-center gap-2",
                            status === 'success' ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                        )}
                    >
                        {status === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        {message}
                    </motion.div>
                )}
            </AnimatePresence>


            <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className={cn(
                    "mt-6 w-full py-2.5 px-4 rounded-xl font-medium text-white shadow-lg transition-all duration-300 flex items-center justify-center gap-2",
                    !file || uploading
                        ? "bg-gray-300 cursor-not-allowed shadow-none"
                        : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-blue-500/30 active:scale-[0.98]"
                )}
            >
                {uploading ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        处理中...
                    </>
                ) : (
                    "开始上传"
                )}
            </button>

            {/* Chunk Display Section */}
            {chunksContent.length > 0 && (
                <div className="mt-8 pt-4 border-t border-gray-100">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-indigo-500" />
                        分块结果预览 ({chunksContent.length})
                    </h3>
                    <div className="space-y-3 max-h-60 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-200">
                        {chunksContent.map((chunk, idx) => (
                            <div key={idx} className="bg-gray-50 p-3 rounded-lg text-xs text-gray-600 border border-gray-100/50 hover:border-indigo-100 transition-colors">
                                <span className="inline-block px-1.5 py-0.5 rounded-md bg-white border border-gray-200 text-[10px] font-mono text-gray-400 mb-1">
                                    Chunk #{idx + 1}
                                </span>
                                <p className="leading-relaxed whitespace-pre-wrap line-clamp-4 hover:line-clamp-none cursor-pointer" title="点击展开">
                                    {chunk}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
