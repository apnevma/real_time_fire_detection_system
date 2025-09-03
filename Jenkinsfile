pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Checkout your GitHub repo into Jenkins workspace
                git branch: 'main', url: 'https://github.com/apnevma/real_time_fire_detection_system.git'
            }
        }

        stage('Build Docker Containers') {
            steps {
                // Run docker compose from the repo root so relative paths work
                dir("${env.WORKSPACE}") {
                    echo "Building and starting Docker containers..."
                    sh 'docker compose -f docker-compose-mongodb.yml -p mongodb up --build -d'
                }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    docker.build('fire-test-image', '-f Dockerfile.testing .').inside {
                    sh "pytest temperature_sensor_simulator/tests/ --junitxml=report_temp.xml || true"
                    sh "pytest humidity_sensor_simulator/tests/ --junitxml=report_humidity.xml || true"
                    }
                }
            }
            post {
                always {
                    junit 'report_*.xml'
                }
            }
        }
    }

    post{
        success {
            echo "Pipeline finished successfully"
        }
        failure {
            echo "Pipeline failed"
        }
    }
}