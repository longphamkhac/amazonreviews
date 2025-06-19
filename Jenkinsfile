pipeline {
    agent any

    options{
        // Max number of build logs to keep and days to keep
        buildDiscarder(logRotator(numToKeepStr: '5', daysToKeepStr: '5'))
        // Enable timestamp at each job in the pipeline
        timestamps()
    }

    environment{
        registryCredential = 'dockerhub'
        flink_registry = 'longpk1/flink_merge_streams'
        spark_registry = 'longpk1/spark_processing'
    }

    stages {
        stage("Building Flink Deployment") {
            steps {
                script {
                    echo "Building image for Flink job ..."
                    dockerImage = docker.build("${flink_registry}:1.0.4", "stream_processing/merge/.")
                    echo "Pushing image to dockerhub ..."
                    docker.withRegistry( '', registryCredential ) {
                        dockerImage.push()
                    }
                    echo "Pushing Flink job image successfully, ready to deploy on k8s ..."
                }
            }
        }
        stage("Submit Flink Job") {
            agent {
                kubernetes {
                    containerTemplate {
                        name 'helm' // Name of the container to be used for helm upgrade
                        image 'longpk1/jenkins:lts' // The image containing helm
                        alwaysPullImage true // Always pull image in case of using the same tag
                    }
                }
            }
            steps {
                script {
                    container("helm") {
                        echo "Grant permissions to access Flink and Spark resources"
                        sh "helm upgrade --install permission helm/permission -n airflow"
                        echo "Grant permissions successfully !!!"
                    }
                }
                script {
                    container("helm") {
                        echo "Ready to submit Flink job ..."
                        sh "kubectl apply -f k8s/flink/flinkapplication/flink-merge-streams.yaml"
                        echo "Submit Flink job successfully !!!"
                    }
                }
            }
        }
    }
}