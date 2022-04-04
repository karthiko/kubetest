pipeline{
    agent any
    stages {
         stage('Build') {
            environment {
                BLUEPRINT_NAME = "test_blueprint_demo_blueprint"
                MORPHEUS_TOKEN = credentials('jenkins-morpheus_token')
                MORPHEUS_URL = "https://core-morpheus.morpheus.r53acpaccenturecloud.net"
            }
            steps {
                sh 'python3 deploy/update_blueprint.py'
            }
        }
        stage('Dev') {
            environment {
				TASK_NAME = "test_python_d_001"
                CLUSTER_NAME = "test_d_cluster_001"
                MORPHEUS_TOKEN = credentials('jenkins-morpheus_token')
                MORPHEUS_URL = "https://core-morpheus.morpheus.r53acpaccenturecloud.net"
            }
            steps {
                sh 'python3 deploy/execute_task.py'
            }
        }
        stage('Production') {
            environment {
                CLUSTER_NAME = "morpheus-eks-test-cluster"
                MORPHEUS_TOKEN = credentials('jenkins-morpheus_token')
                MORPHEUS_URL = "https://core-morpheus.morpheus.r53acpaccenturecloud.net"
                TASK_NAME = "test_python_d_001"
            }
            steps {
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