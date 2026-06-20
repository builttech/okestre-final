# GitHub OAuth Device Flow & Git Branch Actions Integration

Implement the GitHub OAuth Device Flow and a dynamic Git Branch Actions dropdown menu inside the GitIDE dashboard, matching the visual layout, interactions, and user flow shown in the screenshots.

## User Review Required

> [!IMPORTANT]
> The GitHub OAuth client ID used by default is the Dyad client ID (`Ov23liWV2HdC0RBLecWx`). If the user wants to configure their own custom client ID, it can be saved in settings or manually appended to `~/.gitide/config.json` as `github_client_id`.

> [!WARNING]
> Access tokens are stored securely in `~/.gitide/config.json` and are never exposed to the frontend browser client. All GitHub API requests requiring authentication (e.g., listing repositories) are proxied through the local FastAPI backend.

> [!NOTE]
> The branch operations dropdown includes creating new branches, refreshing branch lists, and executing `git pull`. Branch names will be fetched dynamically from the repository.

## Proposed Changes

### Backend Components

---

#### [MODIFY] [main.py](file:///c:/Users/augus/.workspace/gitide/gitide_server/main.py)
- Create helper functions `get_config()` and `save_config(config)` to read and update `~/.gitide/config.json` safely.
- Implement the following new FastAPI endpoints:
  - `POST /api/github/auth/device`: Requests a device and user code from GitHub.
  - `POST /api/github/auth/poll`: Polls GitHub for the access token and saves it in `~/.gitide/config.json`.
  - `GET /api/github/auth/status`: Checks if a token is saved and fetches user profile details from `/user` to display in the UI.
  - `POST /api/github/auth/logout`: Clears the GitHub token from `~/.gitide/config.json`.
  - `GET /api/github/repos`: Proxies the repository list request to GitHub using the stored access token.
  - `GET /api/projects/{project_id}/git/branches`: Retrieves a list of local and remote branches in the repository.
  - `POST /api/projects/{project_id}/git/branches`: Creates a new branch and checks it out.

---

#### [MODIFY] [git_bridge.py](file:///c:/Users/augus/.workspace/gitide/gitide_server/git_bridge.py)
- Implement helper function `get_github_token()` to load the access token from `config.json`.
- Implement `get_authenticated_git_url(url, token)` to insert the OAuth token into the remote URL if it's a GitHub URL.
- Modify `clone_git` to use the authenticated URL.
- Implement `update_remote_url_with_token(repo)` to dynamically update the remote URL of the Git repository with the access token during `deploy_git` and `pull_git` operations.
- Implement `list_branches(project_path)` to retrieve local and remote branches.
- Implement `create_branch(project_path, branch_name)` to create and switch to a new branch.

---

### Frontend Components

---

#### [MODIFY] [index.html](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/index.html)
- Add the HTML structure for the GitHub Connection UI inside the `github-list` tab pane:
  - An authentication container that toggles between logged-out and logged-in states.
  - In the logged-out state: a "Conectar com o GitHub" (Connect to GitHub) button.
  - An instruction panel showing the URL `https://github.com/login/device`, the user code badge (with copy-to-clipboard button), and the status "Aguardando autorização do usuário..." (Waiting for user authorization).
  - In the logged-in state: display user profile info (avatar, username/email) and a "Desconectar" (Logout) button, alongside the list of repositories.
- Modify the branch display in the VCS/Git tab to replace the simple text input with a custom dropdown menu containing:
  - `Create new branch` (with `+` icon)
  - `Refresh branches` (with `rotate` icon)
  - `Git pull` (with `pull` branch icon)

---

#### [MODIFY] [style.css](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/style.css)
- Add styles for the GitHub Connection UI:
  - `.github-auth-card`: Container for the connection flow.
  - `.github-connect-btn`: Styled button with GitHub icon.
  - `.github-code-badge`: Prominent code display container with hover/active states.
  - `.github-profile-bar`: Top bar in the repository tab showing logged-in user profile, avatar, and logout button.
- Add styles for the dropdown menu:
  - `.dropdown-container`: Position relative container for the trigger and floating menu.
  - `.dropdown-menu`: Styled dropdown floating panel with clean border-radius, background, icons, and item hover states matching the screenshot.

---

#### [MODIFY] [app.js](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/app.js)
- Implement the interactive logic for the GitHub flow:
  - Function to fetch auth status on startup and update UI states.
  - Event listener on "Connect to GitHub" button to initiate device flow.
  - Polling loop to check auth status on the backend.
  - Copy-to-clipboard feature for the user authorization code.
  - Updating the "Seus Repositórios do GitHub" listing to call `GET /api/github/repos` and render the fetched items.
- Implement the branch dropdown interaction:
  - Toggle dropdown visibility when clicking the branch button.
  - Implement handlers for "Create new branch", "Refresh branches", and "Git pull".
  - Update local state and console messages upon action completion.

## Verification Plan

### Automated Tests
- Run `python test_api.py` to ensure core VCS functionality remains fully operational.

### Manual Verification
1. Open the "Importar App" modal.
2. Select the "Seus Repositórios do GitHub" tab.
3. Click "Conectar com o GitHub".
4. Verify that the user code is requested and displayed, and polling begins.
5. Copy the code, open `https://github.com/login/device` in a browser, enter the code, and approve.
6. Verify that the UI automatically detects the authorization, logs in, displays user profile, and loads the list of GitHub repositories.
7. Click "Desconectar" and verify that it returns to the logged-out state.
8. Go to the "Controle de Versão (Git)" tab.
9. Click on the branch indicator to open the actions dropdown.
10. Test clicking "Create new branch", type a branch name, and verify that the branch is created and checked out successfully.
11. Test "Refresh branches" and verify it updates the branch status correctly.
12. Test "Git pull" and verify the terminal logs display the pull details.
