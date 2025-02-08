export interface CrawlerConfig {
    module: string;
    class: string;
    login_module: string;
    login_class: string;
    site_id: string;
}

export interface CrawlerBase {
    name: string;
    description?: string;
    homepage: string;
    enabled: boolean;
    config: CrawlerConfig;
}

export interface Crawler extends CrawlerBase {
    id: number;
    created_at: string;
    updated_at: string;
}

export type CreateCrawlerRequest = CrawlerBase;
export type UpdateCrawlerRequest = Partial<CrawlerBase> & { id: number }; 