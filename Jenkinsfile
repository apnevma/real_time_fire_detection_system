pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/apnevma/real_time_fire_detection_system.git'
            }
        }
        stage('Build Docker Conatiners') {
            steps {
                echo "Building and starting Docker containers..."
                sh 'docker compose -f docker-compose-mongodb.yml -p mongodb up --build -d'
            }
        }
        stage('Deploy') {
            steps {
                echo "No deployment step yet: skipping"
            }
        }
        post {
            success {
                echo "Pipeline finished successfully"
            }
            failure {
                echo "Pipeline failed"
        }
    }
    }
}
