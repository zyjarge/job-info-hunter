import api from "./interceptor";
import { Crawler, CreateCrawlerRequest, UpdateCrawlerRequest } from "@/lib/types/crawler";

export async function getCrawlers(): Promise<Crawler[]> {
    const response = await api.get<Crawler[]>("/crawlers");
    return response.data;
}

export async function getCrawler(id: string): Promise<Crawler> {
    const response = await api.get<Crawler>(`/crawlers/${id}`);
    return response.data;
}

export async function createCrawler(data: CreateCrawlerRequest): Promise<Crawler> {
    const response = await api.post<Crawler>("/crawlers", data);
    return response.data;
}

export async function updateCrawler(data: UpdateCrawlerRequest): Promise<Crawler> {
    const response = await api.put<Crawler>(`/crawlers/${data.id}`, data);
    return response.data;
}

export async function deleteCrawler(id: number): Promise<void> {
    await api.delete(`/crawlers/${id}`);
}

export async function toggleCrawlerStatus(id: number): Promise<Crawler> {
    const response = await api.post<Crawler>(`/crawlers/${id}/toggle`);
    return response.data;
} 