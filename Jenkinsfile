class Globals {

    // sets to abort the pipeline if the Sonarqube QualityGate fails
    static boolean qualityGateAbortPipeline = false

}


pipeline {
    agent { label 'podman' }

    options {
        // New jobs should wait until older jobs are finished
        disableConcurrentBuilds()
        // Discard old builds
        buildDiscarder(logRotator(artifactDaysToKeepStr: '7', artifactNumToKeepStr: '1', daysToKeepStr: '45', numToKeepStr: '10'))
        // Timeout the pipeline build after 1 hour
        timeout(time: 1, unit: 'HOURS')
        gitLabConnection('CollabGitLab')
    }

    environment {
        PATH = "$workspace/.venv-mchbuild/bin:$HOME/tools/openshift-client-tools:$HOME/tools/trivy:$PATH"
        KUBECONFIG = "$workspace/.kube/config"
        SCANNER_HOME = tool name: 'Sonarqube-certs-PROD', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
    }

    stages {
        stage('Preflight') {
            steps {
                updateGitlabCommitStatus name: 'Build', state: 'running'

                script {

                    echo '---- INSTALL MCHBUILD ----'

                    sh '''
                    python -m venv .venv-mchbuild
                    PIP_INDEX_URL=https://hub.meteoswiss.ch/nexus/repository/python-all/simple \
                      .venv-mchbuild/bin/pip install --upgrade mchbuild
                    '''
                }
            }
        }


        stage('Test') {
            agent { label 'balfrin' }
            options {
                // GIT Jenkins plugin has configured the MCH Web proxy, which is not accessible from CSCS.
                // Therefore, we need to clone the git repository manually
                skipDefaultCheckout()
            }
            environment {
                MAMBA_ROOT_PREFIX="$SCRATCH/mch_jenkins_node/tools/micromamba"
                PATH="$SCRATCH/mch_jenkins_node/tools/mchbuild/bin:$MAMBA_ROOT_PREFIX/bin:$PATH"
            }
            steps {
                cleanWs()
                echo("---- UPGRADING MCHBUILD AND POETRY ----")
                sh """
                pip install -i https://service.meteoswiss.ch/nexus/repository/python-all/simple --upgrade mchbuild
                pip install -i https://service.meteoswiss.ch/nexus/repository/python-all/simple poetry --upgrade
                """

                echo("---- CLONING GIT REPO ----")
                script {
                    // Jenkins sets PR numbers as branch names if PR is tested
                    // but we always need branch name for git fetch
                    def branch_name = env.CHANGE_ID ? env.CHANGE_BRANCH : env.BRANCH_NAME

                    // TODO TIP-227: Support also version control options: MeteoSwiss Github, Gitlab
                    withCredentials([gitUsernamePassword(credentialsId: 'github app credential for the meteoswiss-apn github organization')]){
                        sh """
                        git init
                        git fetch --no-tags --force --progress -- $GIT_URL ${branch_name}
                        git checkout -f $GIT_COMMIT
                        """
                    }
                }

                echo("---- RUNNING TESTS IN CSCS CONDA VIRTUAL ENVIRONMENT USING MICROMAMBA ----")
                sh "mchbuild conda.build conda.test"
                stash includes: 'test_reports/**', name: 'test_reports'
            }
            post {
                always {
                    sh "mchbuild conda.build.getVersion conda.clean || true"
                    junit keepLongStdio: true, testResults: 'test_reports/junit*.xml'
                }
            }
        }


        stage('Scan') {
            steps {
                unstash 'test_reports'

                echo '---- TYPE CHECK ----'
                script {
                    try {
                        recordIssues(qualityGates: [[threshold: 10, type: 'TOTAL', unstable: false]], tools: [myPy(pattern: 'test_reports/mypy.log')])
                    }
                    catch (err) {
                        error "Too many mypy issues, exiting now..."
                    }
                }


                echo("---- SONARQUBE ANALYSIS ----")
                withSonarQubeEnv("Sonarqube-PROD") {
                    // fix source path in coverage.xml
                    // (required because coverage is calculated using podman which uses a differing file structure)
                    // https://stackoverflow.com/questions/57220171/sonarqube-client-fails-to-parse-pytest-coverage-results
                    sh "sed -i 's/\\/src\\/app-root/.\\//g' test_reports/coverage.xml"
                    sh "${SCANNER_HOME}/bin/sonar-scanner"
                }

                echo("---- SONARQUBE QUALITY GATE ----")
                timeout(time: 1, unit: 'HOURS') {
                    // Parameter indicates whether to set pipeline to UNSTABLE if Quality Gate fails
                    // true = set pipeline to UNSTABLE, false = don't
                    waitForQualityGate abortPipeline: Globals.qualityGateAbortPipeline
                }
            }
        }
    }

    post {
        aborted {
            updateGitlabCommitStatus name: 'Build', state: 'canceled'
        }
        failure {
            updateGitlabCommitStatus name: 'Build', state: 'failed'
            echo 'Sending email'
            sh 'df -h'
            emailext(subject: "${currentBuild.fullDisplayName}: ${currentBuild.currentResult}",
                attachLog: true,
                attachmentsPattern: 'generatedFile.txt',
                body: "Job '${env.JOB_NAME} #${env.BUILD_NUMBER}': ${env.BUILD_URL}",
                recipientProviders: [requestor(), developers()])
        }
        success {
            echo 'Build succeeded'
            updateGitlabCommitStatus name: 'Build', state: 'success'
        }
    }
}
