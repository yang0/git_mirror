from typing import Dict
import asyncio
import git
from pathlib import Path
import logging
import sys
import os
import signal
import subprocess
import re

logger = logging.getLogger(__name__)

class GitMirrorService:
    def __init__(self, mirror_base_path: str, git_daemon_port: int = 9418):
        self.mirror_base_path = Path(mirror_base_path).resolve()
        self.mirror_base_path.mkdir(parents=True, exist_ok=True)
        self.git_daemon_port = git_daemon_port
        self.daemon_process = None
    
    async def create_mirror(self, repo_url: str, repo_name: str) -> Dict:
        """创建公开git仓库镜像
        Args:
            repo_url: 完整的仓库地址 (plugin_key, 如: github.com/yang0/autotask_autogui)
            repo_name: 仓库名称 (plugin_repo_name, 如: autotask_autogui)
        """
        try:
            mirror_path = self.mirror_base_path / repo_name
            
            if mirror_path.exists():
                await self._remove_repo(mirror_path)
                
            # 确保URL格式正确
            if not repo_url.startswith(('http://', 'https://', 'git://')):
                repo_url = f"https://{repo_url}"
                
            logger.info(f"Cloning {repo_url} to {mirror_path}")
            repo = await self._clone_repository(repo_url, mirror_path)
            
            self._setup_git_daemon_export(mirror_path)
            
            clone_url = f"git://localhost:{self.git_daemon_port}/{repo_name}"
            logger.info(f"Mirror created. Clone URL: {clone_url}")
            
            return {
                "status": "success",
                "repo_name": repo_name,
                "mirror_path": str(mirror_path),
                "clone_url": clone_url
            }
            
        except Exception as e:
            logger.error(f"Failed to create mirror: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def _setup_git_daemon_export(self, repo_path: Path):
        """设置仓库为可导出"""
        export_ok = repo_path / 'git-daemon-export-ok'
        export_ok.touch()
        
    async def start_git_daemon(self):
        """启动git daemon服务"""
        if self.daemon_process:
            return
            
        # Windows下使用git的安装路径
        git_exec = "git"  # 确保git在PATH中
        
        cmd = [
            git_exec, 'daemon',
            f'--port={self.git_daemon_port}',
            f'--base-path={self.mirror_base_path}',
            '--export-all',
            '--reuseaddr',
            '--verbose'
        ]
        
        try:
            # Windows下使用CREATE_NEW_CONSOLE标志
            if sys.platform == 'win32':
                self.daemon_process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                self.daemon_process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            logger.info(f"Git daemon started on port {self.git_daemon_port}")
            
        except Exception as e:
            logger.error(f"Failed to start git daemon: {str(e)}", exc_info=True)
            raise
            
    async def stop_git_daemon(self):
        """停止git daemon服务"""
        if self.daemon_process:
            if sys.platform == 'win32':
                self.daemon_process.terminate()
            else:
                self.daemon_process.send_signal(signal.SIGTERM)
            await asyncio.sleep(1)
            self.daemon_process = None
            logger.info("Git daemon stopped")

    async def _clone_repository(self, url: str, path: Path) -> git.Repo:
        """异步克隆仓库"""
        return await asyncio.to_thread(
            git.Repo.clone_from,
            url,
            path,
            mirror=True
        )
        
    async def _remove_repo(self, path: Path):
        """删除仓库"""
        if path.exists():
            await asyncio.to_thread(git.rmtree, path)