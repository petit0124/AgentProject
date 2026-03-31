import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_BASE_URL,
});

export const uploadDocument = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const chatWithBot = async (message: string) => {
    const response = await api.post('/chat', { message });
    return response.data;
};

export const getHistory = async () => {
    const response = await api.get('/history');
    return response.data;
}

export const evaluateRAG = async () => {
    const response = await api.post('/evaluate');
    return response.data;
};
