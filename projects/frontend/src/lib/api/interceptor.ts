import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = "http://localhost:8080/api/v1";

// 创建 axios 实例
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,  // 10 秒超时
    headers: {
        "Content-Type": "application/json",
    },
});

// 请求拦截器
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem("token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // 保存当前页面路径
            const currentPath = window.location.pathname + window.location.search;
            localStorage.setItem("redirectPath", currentPath);
            
            // 清除认证信息
            localStorage.removeItem("token");
            localStorage.removeItem("username");
            
            // 重定向到登录页
            window.location.href = "/auth/login";
            return Promise.reject(new Error("请先登录"));
        }
        return Promise.reject(error);
    }
);

export default api; 