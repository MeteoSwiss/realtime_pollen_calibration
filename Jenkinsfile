class Globals {
    // sets the pipeline to execute all steps related to building the service
    static boolean build = false

    // sets to abort the pipeline if the Sonarqube QualityGate fails
    static boolean qualityGateAbortPipeline = false

    // sets the pipeline to execute all steps related to releasing the service
    static boolean release = false

    // sets the pipeline to execute all steps related to deployment of the service
    static boolean deploy = false

    // sets the pipeline to execute all steps related to delete the service from the container platform
    static boolean deleteContainer = false

    // sets the pipeline to execute all steps related to trigger the security scan
    static boolean runSecurityScan = false

    // the project name in container platform
    static String ocpProject = ''

    // Container deployment environment
    static String deployEnv = ''

    // the image tag used for tagging the image
    static String imageTag = ''

    // the service version
    static String version = ''

}


pipeline {
    agent { label 'podman' }

    parameters {
        choice(choices: ['Build', 'Release', 'Delete', 'Security-Scan'],
            description: 'Build type',
            name: 'buildChoice')

        booleanParam(name: 'PUBLISH_DOCUMENTATION', defaultValue: false, description: 'Publishes the generated documentation')
    }

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
        HTTP_PROXY = 'http://proxy.meteoswiss.ch:8080'
        HTTPS_PROXY = 'http://proxy.meteoswiss.ch:8080'
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
                    echo '---- INITIALIZE PARAMETERS ----'
                    Globals.deployEnv = params.environment
                    Globals.ocpProject = Globals.deployEnv
                        ? sh(script: "mchbuild openshiftExposeProperties -s deploymentEnvironment=${Globals.deployEnv} -g ocpProject",
                             returnStdout: true) : ''
                    // Determine the type of build
                    switch (params.buildChoice) {
                        case 'Build':
                            Globals.build = true
                            break
                        case 'Deploy':
                            Globals.deploy = true
                            break
                        case 'Release':
                            Globals.release = true
                            Globals.build = true
                            break
                        case 'Delete':
                            Globals.deleteContainer = true
                            break
                        case 'Security-Scan':
                            Globals.runSecurityScan = true
                            break
                    }

                    if (Globals.release) {
                        echo '---- TAGGING RELEASE ----'
                        sh 'mchbuild deploy.addNextTag'
                    }

                    if (Globals.build || Globals.deploy || Globals.runSecurityScan) {
                        def versionAndTag = sh(
                            script: 'mchbuild -g version -g image build.getVersion',
                            returnStdout: true
                        ).split('\n')
                        Globals.version = versionAndTag[0]
                        Globals.imageTag = versionAndTag[1]
                        echo "Using version ${Globals.version} and image tag ${Globals.imageTag}"
                    }
                }
            }
        }

        stage('Build') {
            when { expression { Globals.build } }
            steps {
                echo '---- BUILD IMAGE ----'
                sh """
                mchbuild -s version=${Globals.version} -s image=${Globals.imageTag} \
                  build.imageTester
                """
            }
        }

        stage('Test') {
            agent { label 'balfrin' }
            options {
                // GIT Jenkins plugin has configured the MCH Web proxy, which is not accessible from CSCS.
                // Therefore, we need to clone the git repository manually
                skipDefaultCheckout()
            }
            when { expression { Globals.build } }
            environment {
                NO_PROXY = '.meteoswiss.ch,localhost,.cscs.ch,.github.com'
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
                        git clone --no-tags --force --progress -- $GIT_URL ${branch_name}
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
            when { expression { Globals.build } }
            steps {
                unstash 'test_reports'

                echo '---- LINT & TYPE CHECK ----'
                sh "mchbuild -s image=${Globals.imageTag} test.lint"
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




        stage('Create Artifacts') {
            when { expression { Globals.build || Globals.deploy || params.PUBLISH_DOCUMENTATION } }
            steps {
                script {
                    if (Globals.build || Globals.deploy) {
                        echo '---- CREATE IMAGE ----'
                        sh """
                        mchbuild -s version=${Globals.version} -s image=${Globals.imageTag} \
                          build.imageRunner
                        """
                    }
                    if (params.PUBLISH_DOCUMENTATION) {
                        echo '---- CREATE DOCUMENTATION ----'
                        sh """
                        mchbuild -s version=${Globals.version} -s image=${Globals.imageTag} \
                          build.docs
                        """
                    }
                }
            }
        }

        stage('Publish Artifacts') {
            when { expression { Globals.deploy || Globals.release || params.PUBLISH_DOCUMENTATION } }
            environment {
                REGISTRY_AUTH_FILE = "$workspace/.containers/auth.json"
            }
            steps {
                script {
                    if (Globals.deploy || Globals.release) {
                        echo "---- PUBLISH IMAGE ----"
                        withCredentials([usernamePassword(credentialsId: 'openshift-nexus',
                                                          passwordVariable: 'NXPASS',
                                                          usernameVariable: 'NXUSER')]) {
                            sh "mchbuild deploy.image -s fullImageName=${Globals.imageTag}"
                        }
                    }
                }
                script {
                    if (params.PUBLISH_DOCUMENTATION) {
                        echo "---- PUBLISH DOCUMENTATION ----"
                        withCredentials([string(credentialsId: 'documentation-main-prod-token',
                                                variable: 'DOC_TOKEN')]) {
                            sh """
                            mchbuild deploy.docs -s deploymentEnvironment=prod \
                              -s docVersion=${Globals.version}
                            """
                        }
                    }
                }
            }
        }

        stage('Image Security Scan') {
            when {
               expression { Globals.runSecurityScan}
            }
            steps {
                script {
                   echo '---- RUN SECURITY SCAN ----'
                   sh "mchbuild verify.imageSecurityScan -s deploymentEnvironment=${Globals.deployEnv}"
                }
            }
        }

    }


    post {
        cleanup {
            sh """
            mchbuild -s image=${Globals.imageTag} \
                     -s deploymentEnvironment=${Globals.deployEnv} clean
            """
        }
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
