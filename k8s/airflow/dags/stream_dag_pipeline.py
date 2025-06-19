from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime, timedelta
from kubernetes.client.models import V1Volume, V1VolumeMount

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'stream_pipeline_dag',
    default_args=default_args,
    description='A DAG to schedule streaming jobs',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 5, 25),
    catchup=False,
) as dag:

    insert_reviews_task = KubernetesPodOperator(
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_insert_reviews',
        name='insert-reviews',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/insert-reviews.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='stream-yaml',
            mount_path='/insert-reviews.yaml',
            sub_path='insert-reviews.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='stream-yaml',
            config_map={'name': 'insert-reviews'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    insert_metadata_task = KubernetesPodOperator(
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_insert_metadata',
        name='insert-metadata',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/insert-metadata.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='stream-yaml',
            mount_path='/insert-metadata.yaml',
            sub_path='insert-metadata.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='stream-yaml',
            config_map={'name': 'insert-metadata'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    flink_merge_streams_task = KubernetesPodOperator(
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_flink_merge_streams',
        name='flink-merge-streams',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/flink-merge-streams.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='stream-yaml',
            mount_path='/flink-merge-streams.yaml',
            sub_path='flink-merge-streams.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='stream-yaml',
            config_map={'name': 'flink-merge-streams'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    wait_for_flink_merge_streams = KubernetesPodOperator(
        task_id='wait_for_flink_merge_streams',
        name='wait-for-flink-merge-streams',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        cmds=["/bin/bash"],
        arguments=[
            "-c",
            """
            for i in {1..180}; do
                STATUS=$(kubectl get flinkdeployment flink-merge-streams -n processor -o jsonpath='{.status.jobStatus.state}' 2>/dev/null)
                if [ "$STATUS" = "RUNNING" ]; then
                    echo "FlinkDeployment flink-merge-streams completed successfully"
                    exit 0
                fi
                echo "Waiting for spark-flink-merge-streams... (Attempt $i/180)"
                sleep 10
            done
            echo "Timeout waiting for spark-flink-merge-streams to complete"
            exit 1
            """
        ],
        is_delete_operator_pod=False,  # Retain pod for debugging
        get_logs=True,  # Stream logs to Airflow
    )

    spark_streaming_data_task = KubernetesPodOperator(
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_streaming_data',
        name='spark-streaming-data',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/streaming-data.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='spark-yaml',
            mount_path='/streaming-data.yaml',
            sub_path='streaming-data.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='spark-yaml',
            config_map={'name': 'spark-streaming-data'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    [insert_reviews_task, insert_metadata_task] >> flink_merge_streams_task >> wait_for_flink_merge_streams >> spark_streaming_data_task