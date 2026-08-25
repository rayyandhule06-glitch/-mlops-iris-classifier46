# Version Control Workflow — [Project Name] 
## 1. Overview 
This document describes the Git-based version control workflow 
used for this 
Machine Learning project, developed as part of MLOps Lab 
Experiment 2. - **Repository:** https://github.com/<your-username>/ml-mlops
lab2 - **Primary language:** Python - **Maintainer(s):** [Your Name] 
## 2. Branching Strategy 
| Branch            
| 
| Purpose                                             
|--------------------|------------------------------------------------------| 
| `main`             
| 
| `develop`          
development         
| Stable, always-deployable code                       
| Integration branch for day-to-day 
| 
| `feature/<name>`   | Individual features, branched from and 
merged back into `develop` | 
| `conflict-demo-*`  | Demonstration branches created for 
conflict resolution practice | 
**Rule:** No one commits directly to `main`. All changes flow: 
`feature/*` → Pull Request → `develop` → (periodically) merged 
into `main`. 
## 3. Commit Convention 
Commits follow a short, imperative style with a type prefix: 
## feat: add new functionality fix: correct a bug docs: 
documentation changes chore: tooling/config changes refactor: 
code change with no behavior change 
Example: `feat: add classification report to training script` 
## 4. Standard Workflow (Feature Development) 
```bash 
git switch develop 
git pull origin develop 
git switch -c feature/<short-description> 
# ... make changes ... 
git add <files> 
git commit -m "feat: <description>" 
git push -u origin feature/<short-description> 
# Open a Pull Request into `develop` on GitHub 
# After review/approval, merge via GitHub (squash or merge 
commit) 
git branch -d feature/<short-description>          
locally 
# clean up 
git push origin --delete feature/<short-description> # clean up 
remote 
``` 
## 5. Merge Conflict Resolution Process 
1. Attempt the merge/rebase; Git flags conflicting files. 
2. Open each conflicted file and locate `<<<<<<<` / `=======` / 
`>>>>>>>` markers. 
3. Decide which change(s) to keep — current, incoming, or a 
manual combination. 
4. Remove all conflict markers. 
5. `git add <file>` to mark the conflict as resolved. 
6. `git commit` (or continue the rebase) to finalize. 
7. Test the code (`python src/train.py`) before pushing to 
confirm nothing broke. 
## 6. .gitignore Policy for ML Artifacts 
Large or generated files are excluded from Git and are expected 
to be tracked 
separately (e.g., via DVC, cloud storage, or Git-LFS) rather 
than committed directly: - Raw/processed datasets (`data/*.csv`, `data/*.parquet`) - Model checkpoints/binaries (`*.pkl`, `*.h5`, `*.pt`, 
`models/`) - Virtual environments (`.venv/`, `venv/`, `env/`) - Notebook checkpoints (`.ipynb_checkpoints/`) 
## 7. Pull Request Checklist - [ ] Code runs without errors (`python src/train.py`) - [ ] No large data/model files accidentally staged - [ ] Commit messages follow the convention in §3 - [ ] Branch is up to date with `develop` before merging - [ ] PR description explains *what* changed and *why* 
## 8. Verification Log 
| Check                                              
| Status | 
|-----------------------------------------------------|--------| 
| `git --version` ≥ 2.30                              
|  
| `git log --oneline --graph --all` shows merged branches |  
| Repository has 3+ branches                          
| Repository has 1+ merged Pull Request                
| `python src/train.py` runs and prints Accuracy       
## 9. Lessons Learned / Notes 
|  
|  
|  
| 
| 
[Add any project-specific notes here — e.g., recurring conflict 
areas, 
| 
| 
| 
naming conventions adopted, tools used (gh CLI vs web UI), etc.]