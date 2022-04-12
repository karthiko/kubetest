pipeline{
    agent any
    stages {
         stage('Build') {
            environment {
                BLUEPRINT_NAME = "online_beverages"
                MORPHEUS_TOKEN = credentials('jenkins-morpheus_token')
                MORPHEUS_URL = "https://core-morpheus.morpheus.r53acpaccenturecloud.net"
            }
            steps {
                sh 'pip3 install -r requirements.txt'
                sh 'python3 deploy/update_blueprint.py'
            }
        }
        stage('Dev') {
            environment {
				TASK_NAME = "test_python_d_001"
				BLUEPRINT_NAME = "online_beverages"
                CLUSTER_NAME = "demo-cluster-dev-002"
                MORPHEUS_TOKEN = credentials('jenkins-morpheus_token')
                MORPHEUS_URL = "https://core-morpheus.morpheus.r53acpaccenturecloud.net"
                ENV = 'dev'
            }
            steps {
                sh 'python3 deploy/create_cluster.py'
                sh 'python3 deploy/execute_task.py'
            }
        }
        stage('Production') {
            environment {
                BLUEPRINT_NAME = "online_beverages"
                CLUSTER_NAME = "demo-cluster-prod-002"
                MORPHEUS_TOKEN = credentials('jenkins-morpheus_token')
                MORPHEUS_URL = "https://core-morpheus.morpheus.r53acpaccenturecloud.net"
                TASK_NAME = "test_python_d_001"
                ENV = 'prod'
            }
            steps {
                sh 'python3 deploy/create_cluster.py'
                sh 'python3 deploy/execute_task.py'
            }
        }
    }
	post {
        // Clean after build
        always {
            cleanWs()
        }
    }
}
