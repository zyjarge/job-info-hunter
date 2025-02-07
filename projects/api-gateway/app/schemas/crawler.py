from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import pytz


class CrawlerConfig(BaseModel):
    module: str = Field(..., description="爬虫模块名")
    class_: str = Field(..., alias="class", description="爬虫类名")
    login_module: str = Field(..., description="登录模块名")
    login_class: str = Field(..., description="登录类名")
    site_id: str = Field(..., description="网站标识")


class CrawlerBase(BaseModel):
    name: str = Field(..., description="爬虫名称")
    description: Optional[str] = Field(None, description="爬虫描述")
    homepage: str = Field(..., description="目标网站主页")
    enabled: bool = Field(False, description="是否启用")
    config: CrawlerConfig = Field(..., description="爬虫配置")


class CrawlerCreate(CrawlerBase):
    pass


class CrawlerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[CrawlerConfig] = None


class CrawlerInDBBase(CrawlerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=pytz.UTC)
            .astimezone(pytz.timezone("Asia/Shanghai"))
            .isoformat()
        }


class Crawler(CrawlerInDBBase):
    pass
