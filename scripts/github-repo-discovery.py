#!/usr/bin/env python3
"""
GitHub Repo Discovery & Fork Script
Designed for Termux, Linux, or GCP VM
"""

import requests
import json
import subprocess
import os
import sys
from datetime import datetime
from typing import List, Dict

class GitHubRepoDiscovery:
    def __init__(self, github_token: str):
        self.token = github_token
        self.headers = {"Authorization": f"token {github_token}"}
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_repos(self, query: str, language: str = "", stars: str = ">10", 
                     sort: str = "stars", order: str = "desc", per_page: int = 5) -> List[Dict]:
        """
        Search GitHub for repositories
        
        Args:
            query: Search query (e.g., "fastapi telegram bot")
            language: Programming language (e.g., "python")
            stars: Stars filter (e.g., ">100", "10..1000")
            sort: Sort by (stars, forks, updated)
            order: asc or desc
            per_page: Results per page (max 100)
        
        Returns:
            List of repository dictionaries
        """
        search_query = query
        if language:
            search_query += f" language:{language}"
        search_query += f" stars:{stars}"
        
        params = {
            "q": search_query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }
        
        try:
            response = self.session.get(f"{self.base_url}/search/repositories", params=params)
            response.raise_for_status()
            return response.json()["items"]
        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching repos: {e}")
            return []
    
    def fork_repo(self, owner: str, repo: str, org: str = None) -> Dict:
        """
        Fork a repository to your account or organization
        
        Args:
            owner: Repository owner
            repo: Repository name
            org: Optional organization to fork into
        
        Returns:
            Fork response JSON
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/forks"
        data = {}
        if org:
            data["organization"] = org
        
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error forking repo: {e}")
            return {}
    
    def get_repo_details(self, owner: str, repo: str) -> Dict:
        """Get detailed information about a repository"""
        try:
            response = self.session.get(f"{self.base_url}/repos/{owner}/{repo}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching repo details: {e}")
            return {}
    
    def clone_repo(self, url: str, dest: str = None) -> bool:
        """Clone a repository locally"""
        try:
            cmd = ["git", "clone", url]
            if dest:
                cmd.append(dest)
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error cloning repo: {e}")
            return False
    
    def create_workflow_file(self, repo_path: str) -> bool:
        """Create a GitHub Actions workflow for analysis"""
        workflow_dir = os.path.join(repo_path, ".github", "workflows")
        os.makedirs(workflow_dir, exist_ok=True)
        
        workflow_content = """name: Analyze & Rebuild

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Analyze code
        run: |
          npm install
          npm run lint --if-present || true
          npm test --if-present || true
      
      - name: Generate report
        run: echo "Analysis complete" > analysis.txt
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: analysis-report
          path: analysis.txt
"""
        
        workflow_file = os.path.join(workflow_dir, "analyze.yml")
        try:
            with open(workflow_file, "w") as f:
                f.write(workflow_content)
            return True
        except Exception as e:
            print(f"❌ Error creating workflow: {e}")
            return False
    
    def display_repos(self, repos: List[Dict]):
        """Display repositories in a nice format"""
        print("\n" + "="*80)
        print("📦 DISCOVERED REPOSITORIES")
        print("="*80 + "\n")
        
        for idx, repo in enumerate(repos, 1):
            print(f"{idx}. {repo['full_name']}")
            print(f"   ⭐ Stars: {repo['stargazers_count']}")
            print(f"   🍴 Forks: {repo['forks_count']}")
            print(f"   📝 Language: {repo['language'] or 'N/A'}")
            print(f"   📅 Updated: {repo['updated_at']}")
            print(f"   📖 Description: {repo['description'][:80] if repo['description'] else 'No description'}")
            print(f"   🔗 URL: {repo['html_url']}")
            print()
    
    def interactive_menu(self, repos: List[Dict], your_username: str):
        """Interactive menu for selecting and forking repos"""
        if not repos:
            print("❌ No repos found. Try a different search.")
            return
        
        self.display_repos(repos)
        
        while True:
            try:
                choice = input("📍 Select repo to fork (1-5, or 'q' to quit): ").strip().lower()
                
                if choice == 'q':
                    print("👋 Exiting...")
                    break
                
                repo_idx = int(choice) - 1
                if 0 <= repo_idx < len(repos):
                    selected_repo = repos[repo_idx]
                    self.fork_and_prepare(selected_repo, your_username)
                    break
                else:
                    print("❌ Invalid selection. Try again.")
            except ValueError:
                print("❌ Invalid input. Enter a number or 'q'.")
    
    def fork_and_prepare(self, repo: Dict, your_username: str):
        """Fork a repo and prepare it for development"""
        owner = repo['owner']['login']
        repo_name = repo['name']
        
        print(f"\n🔄 Forking {repo['full_name']}...")
        fork_result = self.fork_repo(owner, repo_name)
        
        if fork_result:
            print(f"✅ Forked to {your_username}/{repo_name}")
            print(f"🔗 Fork URL: {fork_result['html_url']}")
            
            # Create workflow
            print("\n📋 Creating GitHub Actions workflow...")
            local_path = f"/tmp/{repo_name}"
            
            if self.clone_repo(fork_result['clone_url'], local_path):
                print(f"✅ Cloned to {local_path}")
                
                if self.create_workflow_file(local_path):
                    print("✅ Created .github/workflows/analyze.yml")
                    print("\n📝 Next steps:")
                    print(f"   1. cd {local_path}")
                    print(f"   2. git add .github/workflows/analyze.yml")
                    print(f"   3. git commit -m 'Add analysis workflow'")
                    print(f"   4. git push origin main")
                    print(f"   5. Open {fork_result['html_url']}/actions to see workflow")
                else:
                    print("⚠️ Workflow creation failed, but fork is ready")
        else:
            print("❌ Fork failed. Check your token and permissions.")

def main():
    """Main entry point"""
    print("🚀 GitHub Repo Discovery & Fork Tool")
    print("="*80)
    
    # Get GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        token = input("🔑 Enter your GitHub Personal Access Token: ").strip()
        if not token:
            print("❌ Token required. Set GITHUB_TOKEN env var or provide it now.")
            sys.exit(1)
    
    # Get username
    your_username = input("👤 Enter your GitHub username: ").strip()
    if not your_username:
        print("❌ Username required.")
        sys.exit(1)
    
    discovery = GitHubRepoDiscovery(token)
    
    # Search loop
    while True:
        print("\n" + "="*80)
        query = input("🔍 What repos do you want to find? (e.g., 'fastapi telegram bot'): ").strip()
        
        if not query:
            print("❌ Please enter a search query.")
            continue
        
        language = input("🗣️ Programming language (press Enter to skip): ").strip() or None
        stars = input("⭐ Minimum stars (default '>10', press Enter to skip): ").strip() or ">10"
        
        print("\n⏳ Searching GitHub...")
        repos = discovery.search_repos(query, language=language or "", stars=stars, per_page=5)
        
        if repos:
            discovery.interactive_menu(repos, your_username)
        
        again = input("\n🔄 Search again? (y/n): ").strip().lower()
        if again != 'y':
            print("👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
