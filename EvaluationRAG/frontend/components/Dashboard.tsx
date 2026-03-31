"use client";

import React, { useState } from 'react';
import { BarChart, Activity, FileText, CheckCircle, RefreshCw } from 'lucide-react';
import { evaluateRAG } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
    BarChart as ReBarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Legend
} from 'recharts';

export default function DashboardComponent() {
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any[]>([]);

    const handleEvaluate = async () => {
        setLoading(true);
        try {
            const results = await evaluateRAG();
            // Transform results for chart if needed
            // Assuming results is an array of objects with metrics
            setData(results);
        } catch (error) {
            console.error(error);
            alert("评估失败，请检查后端日志");
        } finally {
            setLoading(false);
        }
    };

    // Calculate averages for the radar chart
    const averageMetrics = data.length > 0 ? [
        { subject: '相关性', A: data.reduce((acc, curr) => acc + (curr.context_relevancy || 0), 0) / data.length, fullMark: 1 },
        { subject: '精确度', A: data.reduce((acc, curr) => acc + (curr.context_precision || 0), 0) / data.length, fullMark: 1 },
        { subject: '忠实度', A: data.reduce((acc, curr) => acc + (curr.faithfulness || 0), 0) / data.length, fullMark: 1 },
        { subject: '答案相关', A: data.reduce((acc, curr) => acc + (curr.answer_relevancy || 0), 0) / data.length, fullMark: 1 },
    ] : [];

    return (
        <div className="w-full bg-white/50 backdrop-blur-md rounded-2xl border border-gray-100 shadow-xl p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-600" />
                    评估仪表盘
                </h2>
                <button
                    onClick={handleEvaluate}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 shadow-md"
                >
                    <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                    {loading ? "评估中..." : "开始评估"}
                </button>
            </div>

            {data.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-gray-400 bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
                    <BarChart className="w-12 h-12 opacity-20 mb-2" />
                    <p>暂无评估数据，请先进行对话然后点击“开始评估”</p>
                </div>
            ) : (
                <div className="space-y-8">
                    {/* Summary Chart Section */}
                    <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col items-center">
                        <h3 className="text-lg font-semibold text-gray-700 mb-6">综合指标雷达图</h3>
                        <div className="h-80 w-full max-w-2xl">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={averageMetrics}>
                                    <PolarGrid />
                                    <PolarAngleAxis dataKey="subject" />
                                    <PolarRadiusAxis angle={30} domain={[0, 1]} />
                                    <Radar
                                        name="Bot"
                                        dataKey="A"
                                        stroke="#4f46e5"
                                        fill="#4f46e5"
                                        fillOpacity={0.6}
                                    />
                                    <Legend />
                                    <Tooltip />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Detailed Table Section */}
                    <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                        <h3 className="text-lg font-semibold text-gray-700 mb-4">逐条对话详细评分</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-gray-500 border-b border-gray-100 bg-gray-50/50">
                                    <tr>
                                        <th className="px-4 py-3 font-medium w-1/6">问题</th>
                                        <th className="px-4 py-3 font-medium w-1/6">回答</th>
                                        <th className="px-4 py-3 font-medium w-1/3">Context (参考文档)</th>
                                        <th className="px-4 py-3 font-medium text-center">忠实度</th>
                                        <th className="px-4 py-3 font-medium text-center">答案相关</th>
                                        <th className="px-4 py-3 font-medium text-center">上下文相关</th>
                                        <th className="px-4 py-3 font-medium text-center">精确度</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {data.map((row, idx) => (
                                        <tr key={idx} className="group hover:bg-gray-50 transition-colors">
                                            <td className="px-4 py-4 align-top">
                                                <div className="max-h-32 overflow-y-auto pr-2 text-gray-800 font-medium">{row.question}</div>
                                            </td>
                                            <td className="px-4 py-4 align-top">
                                                <div className="max-h-32 overflow-y-auto pr-2 text-gray-600">{row.answer}</div>
                                            </td>
                                            <td className="px-4 py-4 align-top">
                                                <div className="max-h-32 overflow-y-auto pr-2 text-xs text-gray-500 bg-gray-50 p-2 rounded border border-gray-100">
                                                    {Array.isArray(row.contexts) ? row.contexts.map((ctx: string, i: number) => (
                                                        <div key={i} className="mb-2 last:mb-0 pb-2 border-b border-gray-200 last:border-0 border-dashed">
                                                            <span className="font-semibold text-blue-500/50 mr-1">[{i + 1}]</span>
                                                            {ctx}
                                                        </div>
                                                    )) : JSON.stringify(row.contexts)}
                                                </div>
                                            </td>
                                            <td className="px-4 py-4 text-center align-top text-blue-600 font-bold">
                                                {row.faithfulness?.toFixed(2) || "-"}
                                            </td>
                                            <td className="px-4 py-4 text-center align-top text-indigo-600 font-bold">
                                                {row.answer_relevancy?.toFixed(2) || "-"}
                                            </td>
                                            <td className="px-4 py-4 text-center align-top text-purple-600 font-medium">
                                                {row.context_relevancy?.toFixed(2) || "-"}
                                            </td>
                                            <td className="px-4 py-4 text-center align-top text-cyan-600 font-medium">
                                                {row.context_precision?.toFixed(2) || "-"}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
