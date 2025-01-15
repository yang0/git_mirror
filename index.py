import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from gitService import GitMirrorService
from database import get_db
from pluginModel import PluginRepoName
from config import GIT_MIRROR_BASE_PATH, GIT_DAEMON_PORT

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mirror_service = GitMirrorService(GIT_MIRROR_BASE_PATH, git_daemon_port=GIT_DAEMON_PORT)
scheduler = AsyncIOScheduler()

async def check_and_mirror_new_repos(db: Session):
    """检查并镜像新的仓库"""
    try:
        one_hour_ago = datetime.now() - timedelta(hours=1)
        logger.info(f"Checking for new repos created in the last hour: {one_hour_ago}")
        
        new_repos = db.query(PluginRepoName).filter(
            PluginRepoName.created_at >= one_hour_ago
        ).all()
        
        for repo in new_repos:
            logger.debug(f"Processing repo - plugin_repo_name: '{repo.plugin_repo_name}', plugin_key: '{repo.plugin_key}'")
            try:
                result = await mirror_service.create_mirror(
                    repo_url=repo.plugin_key,
                    repo_name=repo.plugin_repo_name
                )
                if result["status"] == "success":
                    if result.get("skipped"):
                        logger.info(f"Mirror already exists: {repo.plugin_repo_name}")
                    else:
                        logger.info(f"Successfully mirrored: {repo.plugin_repo_name}")
                else:
                    logger.error(f"Failed to mirror: {repo.plugin_repo_name}, error: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error mirroring {repo.plugin_repo_name}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in check_and_mirror_new_repos: {str(e)}")

async def update_all_mirrors(db: Session):
    """更新所有仓库的镜像"""
    try:
        all_repos = db.query(PluginRepoName).all()
        logger.info(f"Updating {len(all_repos)} mirrors")
        
        for repo in all_repos:
            logger.debug(f"Updating repo: {repo.plugin_repo_name}")
            try:
                result = await mirror_service.update_mirror(
                    repo_url=repo.plugin_key,
                    repo_name=repo.plugin_repo_name
                )
                if result["status"] == "success":
                    logger.info(f"Successfully updated: {repo.plugin_repo_name}")
                else:
                    logger.error(f"Failed to update: {repo.plugin_repo_name}, error: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error updating {repo.plugin_repo_name}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in update_all_mirrors: {str(e)}")

async def main():
    """主函数"""
    try:
        # 启动git daemon服务
        await mirror_service.start_git_daemon()
        
        # 添加检查新仓库的定时任务
        scheduler.add_job(
            check_and_mirror_new_repos, 
            'interval', 
            minutes=1,
            args=[next(get_db())]
        )
        
        # 添加更新所有仓库的定时任务
        scheduler.add_job(
            update_all_mirrors,
            'interval',
            minutes=1,
            args=[next(get_db())]
        )
        
        scheduler.start()
        
        # 保持程序运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # 停止服务
        await mirror_service.stop_git_daemon()
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())