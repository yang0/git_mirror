# main.py
import uvicorn
from fastapi import FastAPI, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from gitService import GitMirrorService
from database import get_db
from pluginModel import PluginRepoName

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
mirror_service = GitMirrorService("G:/temp/git_mirrors", git_daemon_port=9418)
scheduler = AsyncIOScheduler()

async def check_and_mirror_new_repos(db: Session):
    """检查并镜像新的仓库"""
    try:
        # 获取1小时内的新仓库
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        new_repos = db.query(PluginRepoName).filter(
            PluginRepoName.created_at >= one_hour_ago
        ).all()
        
        for repo in new_repos:
            logger.info(f"Found new repo: {repo.plugin_repo_name}, url: {repo.plugin_key}")
            try:
                result = await mirror_service.create_mirror(
                    repo_url=repo.plugin_key,      # 完整的仓库地址
                    repo_name=repo.plugin_repo_name # 仓库名称
                )
                if result["status"] == "success":
                    logger.info(f"Successfully mirrored: {repo.plugin_repo_name}")
                else:
                    logger.error(f"Failed to mirror: {repo.plugin_repo_name}, error: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error mirroring {repo.plugin_repo_name}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in check_and_mirror_new_repos: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """启动时启动git daemon服务和定时任务"""
    await mirror_service.start_git_daemon()
    
    # 添加定时任务，每分钟运行一次
    scheduler.add_job(
        check_and_mirror_new_repos, 
        'interval', 
        minutes=1,
        args=[next(get_db())]  # 传入数据库会话
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时停止git daemon服务和定时任务"""
    await mirror_service.stop_git_daemon()
    scheduler.shutdown()

@app.post("/mirrors/{url:path}")
async def create_mirror(url: str):
    return await mirror_service.create_mirror(url)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)