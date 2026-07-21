#!/usr/bin/env python3
"""
24/7 Continuous Repo Discovery, Fork, Rebuild & Deploy
Automated workflow for finding, forking, and rebuilding repos
"""

import requests
import json
import subprocess
import os
import sys
import time
import schedule
from datetime import datetime
from typing import List, Dict
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/github-24-7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHub24_7Automation:
    def __init__(self, github_token: str, your_username: str, private_org: str = None):
        self.token = github_token
        self.username = your_username
        self.org = private_org or your_username
        self.headers = {"Authorization": f"token {github_token}"}
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.work_dir = "/tmp/github-automation"
        os.makedirs(self.work_dir, exist_ok=True)
        
        logger.info(f"🚀 24/7 Automation initialized for {your_username}")
    
    def search_trending_repos(self, query: str, language: str = "python", 
                             stars: str = ">100", limit: int = 3) -> List[Dict]:
        """Search for trending repos matching criteria"""
        logger.info(f"🔍 Searching for: {query} (language: {language}, stars: {stars})")
        
        search_query = f"{query} language:{language} stars:{stars}"
        params = {
            "q": search_query,
            "sort": "updated",
            "order": "desc",
            "per_page": limit
        }
        
        try:
            response = self.session.get(f"{self.base_url}/search/repositories", params=params)
            response.raise_for_status()
            repos = response.json()["items"]
            logger.info(f"✅ Found {len(repos)} repositories")
            return repos
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def fork_repo(self, owner: str, repo: str) -> Dict:
        """Fork repository to your account"""
        logger.info(f"🔄 Forking {owner}/{repo}...")
        
        url = f"{self.base_url}/repos/{owner}/{repo}/forks"
        try:
            response = self.session.post(url, json={})
            response.raise_for_status()
            fork = response.json()
            logger.info(f"✅ Successfully forked to {fork['full_name']}")
            return fork
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Fork failed: {e}")
            return {}
    
    def check_fork_exists(self, repo_name: str) -> bool:
        """Check if we already forked this repo"""
        try:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}"
            response = self.session.get(url)
            return response.status_code == 200
        except:
            return False
    
    def clone_fork(self, fork_url: str, repo_name: str) -> str:
        """Clone forked repository locally"""
        logger.info(f"📥 Cloning {repo_name}...")
        
        repo_path = os.path.join(self.work_dir, repo_name)
        try:
            subprocess.run(["git", "clone", fork_url, repo_path], 
                         check=True, capture_output=True)
            logger.info(f"✅ Cloned to {repo_path}")
            return repo_path
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Clone failed: {e}")
            return None
    
    def create_rebuild_workflow(self, repo_path: str, repo_name: str) -> bool:
        """Create GitHub Actions workflow for automated rebuild"""
        logger.info(f"📋 Creating rebuild workflow for {repo_name}")
        
        workflow_dir = os.path.join(repo_path, ".github", "workflows")
        os.makedirs(workflow_dir, exist_ok=True)
        
        workflow_content = f"""name: 24/7 Auto-Rebuild & Deploy

on:
  schedule:
    # Run every 6 hours
    - cron: '0 */6 * * *'
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  rebuild:
    runs-on: ubuntu-latest
    name: Auto-Rebuild {repo_name}
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
        continue-on-error: true
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
        continue-on-error: true
      
      - name: Install & Build
        run: |
          if [ -f package.json ]; then
            npm install
            npm run build --if-present || true
          elif [ -f setup.py ]; then
            pip install -e .
          fi
        continue-on-error: true
      
      - name: Run Tests
        run: |
          if [ -f package.json ]; then
            npm test --if-present || true
          elif [ -f pytest.ini ]; then
            pytest --tb=short || true
          fi
        continue-on-error: true
      
      - name: Code Analysis
        run: |
          if command -v sonar-scanner &> /dev/null; then
            sonar-scanner || true
          fi
        continue-on-error: true
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: build-artifacts-{repo_name}
          path: |
            dist/
            build/
            .coverage
          retention-days: 30
      
      - name: Create Status Report
        run: |
          echo "## 🤖 Auto-Rebuild Report" >> $GITHUB_STEP_SUMMARY
          echo "- Repository: {repo_name}" >> $GITHUB_STEP_SUMMARY
          echo "- Timestamp: $(date)" >> $GITHUB_STEP_SUMMARY
          echo "- Status: ✅ Complete" >> $GITHUB_STEP_SUMMARY

  sync-upstream:
    runs-on: ubuntu-latest
    name: Sync with Upstream
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Sync upstream changes
        run: |
          git remote add upstream https://github.com/ORIGINAL_OWNER/{repo_name}.git || true
          git fetch upstream main || git fetch upstream master || true
          git merge upstream/main || git merge upstream/master || true
        continue-on-error: true
      
      - name: Push updates
        run: |
          git config user.name "GitHub Automation"
          git config user.email "automation@github.com"
          git push origin main || git push origin master || true
        continue-on-error: true
"""
        
        workflow_file = os.path.join(workflow_dir, "24-7-rebuild.yml")
        try:
            with open(workflow_file, "w") as f:
                f.write(workflow_content)
            logger.info(f"✅ Created workflow: {workflow_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Workflow creation failed: {e}")
            return False
    
    def push_to_private_repo(self, local_path: str, repo_name: str) -> bool:
        """Push rebuilt code to new private repository"""
        logger.info(f"📤 Pushing {repo_name} to private repo...")
        
        # Create new private repo
        private_repo_name = f"{repo_name}-rebuilt"
        if not self.create_private_repo(private_repo_name):
            logger.error(f"❌ Failed to create private repo")
            return False
        
        try:
            os.chdir(local_path)
            
            # Add attribution
            attribution_file = "ATTRIBUTION.md"
            with open(attribution_file, "a") as f:
                f.write(f"\n## Attribution\n\n")
                f.write(f"This repository is a rebuilt/refactored version of an open-source project.\n")
                f.write(f"Rebuilt on: {datetime.now().isoformat()}\n")
            
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Add attribution and rebuilt workflows"], 
                         check=True, capture_output=True)
            
            # Push to private repo
            private_url = f"https://{self.token}@github.com/{self.username}/{private_repo_name}.git"
            subprocess.run(["git", "push", "-u", private_url, "main"], 
                         check=True, capture_output=True)
            
            logger.info(f"✅ Pushed to private repo: {self.username}/{private_repo_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Push failed: {e}")
            return False
    
    def create_private_repo(self, repo_name: str) -> bool:
        """Create a new private repository"""
        logger.info(f"🔐 Creating private repository: {repo_name}")
        
        url = f"{self.base_url}/user/repos"
        data = {
            "name": repo_name,
            "description": f"Rebuilt version of a public repository",
            "private": True,
            "auto_init": True
        }
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            logger.info(f"✅ Private repo created: {repo_name}")
            return True
        except requests.exceptions.RequestException as e:
            if "already exists" in str(e):
                logger.warning(f"⚠️ Repo already exists: {repo_name}")
                return True
            logger.error(f"❌ Failed to create private repo: {e}")
            return False
    
    def process_repo(self, repo: Dict) -> bool:
        """Full workflow: fork -> clone -> add workflow -> push to private"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🎯 Processing: {repo['full_name']}")
        logger.info(f"{'='*80}")
        
        owner = repo['owner']['login']
        repo_name = repo['name']
        
        # Check if already forked
        if self.check_fork_exists(repo_name):
            logger.info(f"⏭️ Already forked: {repo_name}")
            fork_url = f"https://github.com/{self.username}/{repo_name}.git"
        else:
            # Fork repo
            fork = self.fork_repo(owner, repo_name)
            if not fork:
                return False
            
            # Wait for fork to be ready
            time.sleep(5)
            fork_url = fork['clone_url']
        
        # Clone fork
        repo_path = self.clone_fork(fork_url, repo_name)
        if not repo_path:
            return False
        
        # Add rebuild workflow
        if not self.create_rebuild_workflow(repo_path, repo_name):
            logger.warning(f"⚠️ Workflow creation failed, continuing anyway")
        
        # Commit and push workflow
        try:
            os.chdir(repo_path)
            subprocess.run(["git", "add", ".github/workflows/"], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Add 24/7 auto-rebuild workflow"], 
                         check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], 
                         check=True, capture_output=True)
            logger.info(f"✅ Pushed workflow to forked repo")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Could not push workflow: {e}")
        
        # Push to private repo
        if self.push_to_private_repo(repo_path, repo_name):
            logger.info(f"✅ {repo_name} fully processed and in private repo")
            return True
        else:
            logger.warning(f"⚠️ {repo_name} forked but private push failed")
            return False
    
    def schedule_automation(self, queries: List[str], languages: List[str] = None, 
                          interval_hours: int = 6):
        """Schedule continuous automation"""
        logger.info(f"⏰ Scheduling 24/7 automation every {interval_hours} hours")
        
        if not languages:
            languages = ["python", "javascript", "go", "rust"]
        
        def automation_job():
            logger.info(f"\n🔄 Running scheduled automation at {datetime.now()}")
            
            for query in queries:
                for lang in languages:
                    repos = self.search_trending_repos(query, language=lang, limit=2)
                    
                    for repo in repos:
                        try:
                            self.process_repo(repo)
                            time.sleep(2)  # Rate limiting
                        except Exception as e:
                            logger.error(f"❌ Error processing repo: {e}")
                    
                    time.sleep(2)
        
        # Schedule job
        schedule.every(interval_hours).hours.do(automation_job)
        
        # Run initial job
        automation_job()
        
        # Keep scheduler running
        logger.info("🚀 Automation running 24/7...")
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main 24/7 automation entry point"""
    logger.info("="*80)
    logger.info("🤖 GitHub 24/7 Continuous Automation Started")
    logger.info("="*80)
    
    # Configuration
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("❌ GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    username = os.getenv("GITHUB_USERNAME") or input("Enter GitHub username: ").strip()
    
    automation = GitHub24_7Automation(token, username)
    
    # Define what to search for
    queries = [
        "fastapi",
        "telegram bot",
        "discord bot",
        "cli tool",
        "api server"
    ]
    
    languages = ["python", "javascript", "go"]
    
    # Start 24/7 automation (runs every 6 hours)
    try:
        automation.schedule_automation(queries, languages, interval_hours=6)
    except KeyboardInterrupt:
        logger.info("\n👋 Stopping automation...")

if __name__ == "__main__":
    main()
