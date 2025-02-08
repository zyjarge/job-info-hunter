import api from "./interceptor";
import Cookies from "js-cookie";
import { AxiosError } from "axios";

interface LoginRequest {
    username: string;
    password: string;
}

interface LoginResponse {
    access_token: string;
    token_type: string;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
    const params = new URLSearchParams();
    params.append("username", data.username);
    params.append("password", data.password);
    
    try {
        const response = await api.post<LoginResponse>(`/token`, params, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        });

        // 同时设置localStorage和cookie
        localStorage.setItem("token", response.data.access_token);
        Cookies.set("token", response.data.access_token, { expires: 7 }); // 7天过期

        return response.data;
    } catch (error) {
        if (error instanceof AxiosError) {
            if (error.response) {
                // 服务器返回了错误响应
                throw new Error(error.response.data?.detail || "登录失败，请检查用户名和密码");
            } else if (error.request) {
                // 请求已发出，但没有收到响应
                throw new Error("无法连接到服务器，请检查网络连接");
            }
        }
        // 其他错误
        throw new Error("登录请求失败，请稍后重试");
    }
}

export function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
} 