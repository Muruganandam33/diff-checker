// Jenkins runs directly inside Ubuntu/WSL2, so it can use the same
// docker, ansible-playbook, terraform, kubectl and k3s commands as you.
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        APP_IMAGE     = 'diff-checker-app:1.0'
        TEST_IMAGE    = 'diff-checker-tests:1.0'
        APP_CONTAINER = 'diff-checker-app'   // also the hostname the tests use
        NETWORK       = 'diffnet'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Flask Docker image') {
            steps {
                sh 'docker build -f docker/Dockerfile.app -t $APP_IMAGE .'
            }
        }

        stage('Start Flask application container') {
            steps {
                sh '''
                    docker network inspect $NETWORK >/dev/null 2>&1 || docker network create $NETWORK
                    docker rm -f $APP_CONTAINER || true
                    docker run -d --name $APP_CONTAINER --network $NETWORK \
                        -e APP_ENV=development -e APP_MESSAGE="Diff Checker" -e APP_VERSION=1.0 \
                        $APP_IMAGE
                '''
            }
        }

        stage('Build Playwright test Docker image') {
            steps {
                sh 'docker build -f docker/Dockerfile.tests -t $TEST_IMAGE .'
            }
        }

        stage('Run headless Playwright tests') {
            steps {
                sh '''
                    docker run --rm --ipc=host --network $NETWORK \
                        -e BASE_URL=http://$APP_CONTAINER:5000 \
                        $TEST_IMAGE
                '''
            }
        }

        stage('Stop and remove containers') {
            steps {
                sh '''
                    docker rm -f $APP_CONTAINER || true
                    docker network rm $NETWORK || true
                '''
            }
        }

        stage('Run Ansible configuration') {
            steps {
                sh 'ansible-playbook -i ansible/inventory.ini ansible/playbook.yml'
            }
        }

        stage('Import image into K3s') {
            steps {
                // K3s uses containerd, so it cannot see Docker images until we import them
                sh 'docker save $APP_IMAGE | sudo -n /usr/local/bin/k3s ctr images import -'
            }
        }

        stage('Terraform init') {
            steps {
                dir('terraform') {
                    sh 'terraform init -input=false'
                }
            }
        }

        stage('Terraform validate') {
            steps {
                dir('terraform') {
                    sh 'terraform validate'
                }
            }
        }

        stage('Terraform plan') {
            steps {
                dir('terraform') {
                    sh 'terraform plan -input=false -out=tfplan'
                }
            }
        }

        stage('Terraform apply') {
            steps {
                dir('terraform') {
                    sh 'terraform apply -input=false -auto-approve tfplan'
                }
            }
        }

        stage('Verify Kubernetes deployment') {
            steps {
                sh '''
                    # restart so pods always use the image that was just imported
                    kubectl -n diff-checker rollout restart deployment/diff-checker
                    kubectl -n diff-checker rollout status deployment/diff-checker --timeout=120s
                    kubectl -n diff-checker get pods,svc
                    curl -fsS --retry 10 --retry-connrefused --retry-delay 3 http://localhost:30080/health
                '''
            }
        }
    }

    post {
        always {
            // Safety net: clean up even when a stage fails
            sh '''
                docker rm -f $APP_CONTAINER || true
                docker network rm $NETWORK || true
            '''
        }
        success {
            echo 'Pipeline finished. Open http://localhost:30080'
        }
        failure {
            echo 'Pipeline failed. Read the console output above the red stage.'
        }
    }
}
