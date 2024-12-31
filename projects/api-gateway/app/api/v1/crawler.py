from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.crud import crawler as crawler_crud
from app.schemas.crawler import Crawler, CrawlerCreate, CrawlerUpdate
from app.schemas.user import User

router = APIRouter()


@router.get("/crawlers", response_model=List[Crawler], summary="获取爬虫列表")
async def get_crawlers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> List[Crawler]:
    """
    获取爬虫列表

    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    return crawler_crud.get_crawlers(db, skip=skip, limit=limit)


@router.post("/crawlers", response_model=Crawler, summary="创建爬虫")
async def create_crawler(
    crawler: CrawlerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Crawler:
    """
    创建新的爬虫

    - **name**: 爬虫名称（必填，唯一）
    - **description**: 爬虫描述（选填）
    - **homepage**: 目标网站主页（必填）
    - **enabled**: 是否启用（默认为 false）
    - **config**: 爬虫配置（必填）
        - **module**: 爬虫模块名
        - **class**: 爬虫类名
        - **login_module**: 登录模块名
        - **login_class**: 登录类名
        - **site_id**: 网站标识
    """
    db_crawler = crawler_crud.get_crawler_by_name(db, name=crawler.name)
    if db_crawler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="爬虫名称已存在",
        )
    return crawler_crud.create_crawler(db=db, crawler=crawler)


@router.get("/crawlers/{crawler_id}", response_model=Crawler, summary="获取爬虫详情")
async def get_crawler(
    crawler_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Crawler:
    """
    根据 ID 获取爬虫详情

    - **crawler_id**: 爬虫 ID
    """
    db_crawler = crawler_crud.get_crawler(db, crawler_id=crawler_id)
    if not db_crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="爬虫不存在",
        )
    return db_crawler


@router.put("/crawlers/{crawler_id}", response_model=Crawler, summary="更新爬虫")
async def update_crawler(
    crawler_id: int,
    crawler: CrawlerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Crawler:
    """
    更新爬虫信息

    - **crawler_id**: 爬虫 ID
    - **name**: 爬虫名称（选填）
    - **description**: 爬虫描述（选填）
    - **homepage**: 目标网站主页（选填）
    - **enabled**: 是否启用（选填）
    - **config**: 爬虫配置（选填）
        - **module**: 爬虫模块名
        - **class**: 爬虫类名
        - **login_module**: 登录模块名
        - **login_class**: 登录类名
        - **site_id**: 网站标识
    """
    db_crawler = crawler_crud.update_crawler(db, crawler_id=crawler_id, crawler=crawler)
    if not db_crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="爬虫不存在",
        )
    return db_crawler


@router.delete("/crawlers/{crawler_id}", summary="删除爬虫")
async def delete_crawler(
    crawler_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    删除爬虫

    - **crawler_id**: 爬虫 ID
    """
    if not crawler_crud.delete_crawler(db, crawler_id=crawler_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="爬虫不存在",
        )
    return {"message": "爬虫已删除"}


@router.post(
    "/crawlers/{crawler_id}/toggle", response_model=Crawler, summary="切换爬虫状态"
)
async def toggle_crawler_status(
    crawler_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Crawler:
    """
    切换爬虫的启用状态

    - **crawler_id**: 爬虫 ID
    """
    db_crawler = crawler_crud.get_crawler(db, crawler_id=crawler_id)
    if not db_crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="爬虫不存在",
        )

    # 切换状态
    return crawler_crud.update_crawler(
        db,
        crawler_id=crawler_id,
        crawler=CrawlerUpdate(enabled=not db_crawler.enabled),
    )
