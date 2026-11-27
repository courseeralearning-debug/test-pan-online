// Multibranch pipeline
//   every branch / PR : setup -> quality gates -> unit -> smoke
//   main              : same + regression, Slack on every result
//   failures          : Slack + email (culprits, team list)

pipeline {
  agent { label 'linux' }

  options {
    timestamps()
    timeout(time: 60, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '30'))
    disableConcurrentBuilds(abortPrevious: true)   // new push cancels the older build of the same branch
  }

  parameters {
    choice(name: 'TARGET_ENV', choices: ['auto', 'dev', 'staging'],
           description: 'auto = staging for main, dev for other branches. Prod is NOT deployable from here.')
    booleanParam(name: 'FORCE_REGRESSION', defaultValue: false,
                 description: 'Also run regression on a non-main branch')
  }

  environment {
    SLACK_CHANNEL = '#ci-alerts'
    CI_EMAIL      = 'qa-team@example.com'
    PY            = '.venv/bin'
  }

  stages {
    stage('Setup') {
      steps {
        script {
          env.DEPLOY_ENV = params.TARGET_ENV == 'auto'
              ? (env.BRANCH_NAME == 'main' ? 'staging' : 'dev')
              : params.TARGET_ENV
          currentBuild.description = "${env.BRANCH_NAME} -> ${env.DEPLOY_ENV}"
        }
        sh '''
          rm -rf reports && mkdir -p reports
          python3 -m venv .venv
          .venv/bin/pip install -q --upgrade pip
          .venv/bin/pip install -q -r requirements.txt -r requirements-dev.txt
        '''
      }
    }

    stage('Quality gates') {
      failFast true
      parallel {
        stage('Lint')         { steps { sh '$PY/ruff check . && $PY/ruff format --check .' } }
        stage('Type check')   { steps { sh '$PY/mypy src' } }
        stage('Security')     { steps { sh '$PY/bandit -q -r src -ll' } }          // medium+ severity fails
        stage('Dependencies') { steps { sh '$PY/pip-audit -r requirements.txt' } } // known CVEs fail
      }
    }

    stage('Unit tests') {
      steps {
        sh '''$PY/pytest tests/unit -q --junitxml=reports/junit-unit.xml \
              --cov=src --cov-report=xml:reports/coverage.xml --cov-fail-under=80'''
      }
    }

    stage('Smoke') {
      steps {
        withCredentials([string(credentialsId: "${env.DEPLOY_ENV}-api-token", variable: 'API_TOKEN')]) {
          sh '$PY/pytest -m smoke -q --junitxml=reports/junit-smoke.xml'
        }
      }
    }

    stage('Regression') {
      when { anyOf { branch 'main'; expression { params.FORCE_REGRESSION } } }
      steps {
        withCredentials([string(credentialsId: "${env.DEPLOY_ENV}-api-token", variable: 'API_TOKEN')]) {
          sh '$PY/pytest -m regression -q -n auto --junitxml=reports/junit-regression.xml'
        }
      }
    }
  }

  post {
    always   { junit allowEmptyResults: true, testResults: 'reports/junit-*.xml' }
  }
}
