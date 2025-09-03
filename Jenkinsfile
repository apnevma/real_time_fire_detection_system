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
                dir("${env.WORKSPACE}/temperature_sensor_simulator") {
                    sh 'pytest tests/ --maxfail=1 --disable-warnings -q'
                }
                dir("${env.WORKSPACE}/humidity_sensor_simulator") {
                    sh 'pytest tests/ --maxfail=1 --disable-warnings -q'
                }
            }
        }
        stage('Deploy') {
            steps {
                echo "No deployment step yet — skipping."
            }
        }
    }
    
    post {
        always {
            junit 'report.xml'
        }
        success {
            echo "Pipeline finished successfully"
        }
        failure {
            echo "Pipeline failed"
        }
    }
}