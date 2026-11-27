# Very Important workflow
# CI pipeline: Jenkins + Slack

## Flow
| Trigger | Stages |
|---|---|
| Push to any branch / PR | Setup → Lint ∥ Type check ∥ Security ∥ Dependency CVEs → Unit (cov ≥ 80%) → Smoke |
| Merge to `main` | Same as above (re-run) → **Regression** → Slack (always) |
| Any failure / unstable | Slack + email (committers, team list, whoever triggered it) |

## Layout
```
ci-pipeline/                                 # app repo (Jenkins builds this)
├── Jenkinsfile
├── src/qa_client/                           # sample API client + validators
├── tests/unit/                              # no network, coverage gate
├── tests/smoke/                             # @smoke, every branch
├── tests/regression/                        # @regression, main only
├── conftest.py, pytest.ini, ruff.toml
├── requirements.txt, requirements-dev.txt
├── config/dev.env, config/staging.env       # non-secret settings only
└── slack_bot/bot.py                         # runs as a service, not in CI
jenkins-shared-lib/                          # separate repo
└── vars/notifyBuild.groovy
```

Agent prerequisite (Ubuntu): `sudo apt install -y python3-venv python3-pip git`.
Without `python3-venv` the Setup stage fails with `ensurepip is not available`.

Local check before pushing (same commands as Jenkins):
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy src \
  && .venv/bin/bandit -q -r src -ll && .venv/bin/pip-audit -r requirements.txt \
  && .venv/bin/pytest tests/unit --cov=src --cov-fail-under=80 \
  && .venv/bin/pytest -m smoke
```

## 1. Jenkins plugins
Pipeline, Pipeline: Multibranch, GitHub Branch Source (or GitLab/Bitbucket equivalent),
Credentials Binding, JUnit, Timestamper, Slack Notification, Email Extension.

## 2. Job
New Item → **Multibranch Pipeline** → Branch source = your repo → Discover branches + PRs.
Add a webhook from the repo to `https://<jenkins>/github-webhook/` so pushes trigger builds immediately.

**Only allow tested code into main** (done in the Git host, not Jenkins):
branch protection on `main` → require a PR → require the Jenkins status check
(`continuous-integration/jenkins/pr-merge`) → block direct pushes.

## 3. Environments and secrets
- **Non-secrets** (URLs, timeouts) → `config/<env>.env` in the repo.
- **Secrets** → Jenkins credentials (*Secret text*), ID format `<env>-api-token`
  (`dev-api-token`, `staging-api-token`). Put them in **folder-scoped** credentials
  (job folder → Credentials) so other teams' jobs can't read them.
- Used only through `withCredentials` with **single-quoted** `sh` strings,
  so Groovy never interpolates them and Jenkins masks them in logs.
- **Prod** is intentionally not a choice. Deploy prod from a separate job with
  an `input` approval step and its own credentials.
- More environments: add `config/qa.env`, a `qa-api-token` credential and `'qa'` to
  the `TARGET_ENV` choices (and to `ALLOWED_ENVS` in the bot).

## 4. Shared library
Push `vars/notifyBuild.groovy` to its own repo, then
Manage Jenkins → System → **Global Trusted Pipeline Libraries** → name `ci-shared`,
default version `main`, point it at that repo. `@Library('ci-shared') _` loads it.

## 5. Slack + email
- Slack: create a Slack app with bot scope `chat:write` and invite it to `#ci-alerts`.
  Manage Jenkins → System → Slack → workspace + credential (Secret text = `xoxb-…` bot token).
- Email: Manage Jenkins → System → Extended E-mail Notification → SMTP server and credentials.
- Change `SLACK_CHANNEL` and `CI_EMAIL` at the top of the Jenkinsfile.

## 6. Slack bot (trigger builds from Slack)
1. In the same Slack app: enable **Socket Mode** (creates an `xapp-…` token with `connections:write`),
   add slash command `/jenkins`, add bot scope `commands`, reinstall the app.
2. In Jenkins create a user `slack-bot` with **only** Job/Read + Job/Build on this job's folder
   (Matrix or Role-based authorization), then generate an API token for it.
3. Run the bot:
   ```bash
   python3 -m venv ~/slackbot && ~/slackbot/bin/pip install -r slack_bot/requirements.txt
   ```
   `/etc/systemd/system/jenkins-slackbot.service`:
   ```ini
   [Unit]
   Description=Jenkins Slack bot
   After=network-online.target

   [Service]
   User=jenkins
   EnvironmentFile=/etc/jenkins-slackbot.env
   ExecStart=/home/jenkins/slackbot/bin/python /home/jenkins/slack_bot/bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   `/etc/jenkins-slackbot.env` (`chmod 600`, owned by root):
   ```
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   JENKINS_URL=https://jenkins.example.com
   JENKINS_USER=slack-bot
   JENKINS_API_TOKEN=...
   ALLOWED_SLACK_USERS=U012ABCDEF,U034GHIJKL
   ALLOWED_JOBS=my-app
   ```
   `sudo systemctl daemon-reload && sudo systemctl enable --now jenkins-slackbot`
4. In Slack:
   ```
   /jenkins build my-app                       # main, auto env (staging)
   /jenkins build my-app feature/login dev     # branch on dev
   /jenkins build my-app feature/login dev regression
   /jenkins status my-app main
   ```

## Notes
- A branch must have built once (from a push) before `buildWithParameters` works for it,
  because Jenkins only learns the parameters from the first run.
- Socket Mode means the bot needs no inbound port or public URL.
- Put Jenkins behind HTTPS. API tokens and webhooks shouldn't travel over plain HTTP.
- `src/`, `tests/unit/` and the 80% coverage gate are assumptions. Adjust them to your repo.
