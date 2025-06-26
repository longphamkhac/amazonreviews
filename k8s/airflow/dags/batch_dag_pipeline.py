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
    'spark_pipeline_dag',
    default_args=default_args,
    description='A DAG to schedule Spark jobs',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 5, 25),
    catchup=False,
) as dag:

    spark_raw2delta_avro_task = KubernetesPodOperator(
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_raw2delta_avro',
        name='spark-raw2delta-avro',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/raw2delta-avro.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='spark-yaml',
            mount_path='/raw2delta-avro.yaml',
            sub_path='raw2delta-avro.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='spark-yaml',
            config_map={'name': 'spark-raw2delta-avro'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    wait_for_raw2delta_avro = KubernetesPodOperator(
        task_id='wait_for_raw2delta_avro',
        name='wait-for-raw2delta-avro',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        cmds=["/bin/bash"],
        arguments=[
            "-c",
            """
            for i in {1..12000}; do
                STATUS=$(kubectl get sparkapplication spark-raw2delta-avro -n processor -o jsonpath='{.status.applicationState.state}' 2>/dev/null)
                if [ "$STATUS" = "COMPLETED" ]; then
                    echo "SparkApplication spark-raw2delta-avro completed successfully"
                    exit 0
                elif [ "$STATUS" = "FAILED" ]; then
                    echo "SparkApplication spark-raw2delta-avro failed"
                    exit 1
                fi
                echo "Waiting for spark-raw2delta-avro... (Attempt $i/12000)"
                sleep 10
            done
            echo "Timeout waiting for spark-raw2delta-avro to complete"
            exit 1
            """
        ],
        is_delete_operator_pod=False,  # Retain pod for debugging
        get_logs=True,  # Stream logs to Airflow
    )

    spark_merge2delta_task = KubernetesPodOperator(
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_spark_merge2delta',
        name='spark-merge2delta',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/merge2delta.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='spark-yaml',
            mount_path='/merge2delta.yaml',
            sub_path='merge2delta.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='spark-yaml',
            config_map={'name': 'spark-merge2delta'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    wait_for_merge2delta = KubernetesPodOperator(
        task_id='wait_for_merge2delta',
        name='wait-for-merge2delta',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        cmds=["/bin/bash"],
        arguments=[
            "-c",
            """
            for i in {1..12000}; do
                STATUS=$(kubectl get sparkapplication spark-merge2delta -n processor -o jsonpath='{.status.applicationState.state}' 2>/dev/null)
                if [ "$STATUS" = "COMPLETED" ]; then
                    echo "SparkApplication spark-merge2delta completed successfully"
                    exit 0
                elif [ "$STATUS" = "FAILED" ]; then
                    echo "SparkApplication spark-merge2delta failed"
                    exit 1
                fi
                echo "Waiting for spark-merge2delta... (Attempt $i/12000)"
                sleep 10
            done
            echo "Timeout waiting for spark-merge2delta to complete"
            exit 1
            """
        ],
        is_delete_operator_pod=False,  # Retain pod for debugging
        get_logs=True,  # Stream logs to Airflow
    )

    spark_adding_uuidv7_task = KubernetesPodOperator(
        # namespace='spark-operator',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_adding_uuidv7',
        name='spark-adding-uuidv7',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/adding-uuidv7.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='spark-yaml',
            mount_path='/adding-uuidv7.yaml',
            sub_path='adding-uuidv7.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='spark-yaml',
            config_map={'name': 'spark-adding-uuidv7'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    wait_for_adding_uuidv7 = KubernetesPodOperator(
        task_id='wait_for_adding_uuidv7',
        name='wait-for-adding-uuidv7',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        cmds=["/bin/bash"],
        arguments=[
            "-c",
            """
            for i in {1..12000}; do
                STATUS=$(kubectl get sparkapplication spark-adding-uuidv7 -n processor -o jsonpath='{.status.applicationState.state}' 2>/dev/null)
                if [ "$STATUS" = "COMPLETED" ]; then
                    echo "SparkApplication spark-adding-uuidv7 completed successfully"
                    exit 0
                elif [ "$STATUS" = "FAILED" ]; then
                    echo "SparkApplication spark-adding-uuidv7 failed"
                    exit 1
                fi
                echo "Waiting for spark-adding-uuidv7... (Attempt $i/12000)"
                sleep 10
            done
            echo "Timeout waiting for spark-adding-uuidv7 to complete"
            exit 1
            """
        ],
        is_delete_operator_pod=False,  # Retain pod for debugging
        get_logs=True,  # Stream logs to Airflow
    )

    spark_generate_silver_schema_task = KubernetesPodOperator(
        # namespace='spark-operator',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_generate_silver_schema',
        name='spark-generate-silver-schema',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/generate-silver-schema.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='spark-yaml',
            mount_path='/generate-silver-schema.yaml',
            sub_path='generate-silver-schema.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='spark-yaml',
            config_map={'name': 'spark-generate-silver-schema'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    # wait_for_generate_silver_schema = KubernetesPodOperator(
    #     task_id='wait_for_generate_silver_schema',
    #     name='wait-for-generate-silver-schema',
    #     namespace='airflow',
    #     image='bitnami/kubectl:latest',
    #     cmds=["/bin/bash"],
    #     arguments=[
    #         "-c",
    #         """
    #         for i in {1..18000}; do
    #             STATUS=$(kubectl get sparkapplication spark-generate-silver-schema -n processor -o jsonpath='{.status.applicationState.state}' 2>/dev/null)
    #             if [ "$STATUS" = "COMPLETED" ]; then
    #                 echo "SparkApplication spark-generate-silver-schema completed successfully"
    #                 exit 0
    #             elif [ "$STATUS" = "FAILED" ]; then
    #                 echo "SparkApplication spark-generate-silver-schema failed"
    #                 exit 1
    #             fi
    #             echo "Waiting for spark-generate-silver-schema... (Attempt $i/18000)"
    #             sleep 10
    #         done
    #         echo "Timeout waiting for spark-generate-silver-schema to complete"
    #         exit 1
    #         """
    #     ],
    #     is_delete_operator_pod=False,  # Retain pod for debugging
    #     get_logs=True,  # Stream logs to Airflow
    # )

    spark_generate_data_mart_task = KubernetesPodOperator(
        # namespace='spark-operator',
        namespace='airflow',
        image='bitnami/kubectl:latest',
        task_id='submit_generate_data_mart',
        name='spark-generate-data-mart',
        cmds=["kubectl"],
        arguments=["apply", "-f", "/generate-data-mart.yaml"],
        config_file=None,
        volume_mounts=[V1VolumeMount(
            name='spark-yaml',
            mount_path='/generate-data-mart.yaml',
            sub_path='generate-data-mart.yaml',
            read_only=True
        )],
        volumes=[V1Volume(
            name='spark-yaml',
            config_map={'name': 'spark-generate-data-mart'}
        )],
        is_delete_operator_pod=False,
        get_logs=True
    )

    # wait_for_generate_data_mart = KubernetesPodOperator(
    #     task_id='wait_for_generate_data_mart',
    #     name='wait-for-generate-data-mart',
    #     namespace='airflow',
    #     image='bitnami/kubectl:latest',
    #     cmds=["/bin/bash"],
    #     arguments=[
    #         "-c",
    #         """
    #         for i in {1..18000}; do
    #             STATUS=$(kubectl get sparkapplication spark-generate-data-mart -n processor -o jsonpath='{.status.applicationState.state}' 2>/dev/null)
    #             if [ "$STATUS" = "COMPLETED" ]; then
    #                 echo "SparkApplication spark-generate-data-mart completed successfully"
    #                 exit 0
    #             elif [ "$STATUS" = "FAILED" ]; then
    #                 echo "SparkApplication spark-generate-data-mart failed"
    #                 exit 1
    #             fi
    #             echo "Waiting for spark-generate-data-mart... (Attempt $i/18000)"
    #             sleep 10
    #         done
    #         echo "Timeout waiting for spark-generate-data-mart to complete"
    #         exit 1
    #         """
    #     ],
    #     is_delete_operator_pod=False,  # Retain pod for debugging
    #     get_logs=True,  # Stream logs to Airflow
    # )

    spark_raw2delta_avro_task >> wait_for_raw2delta_avro >> spark_merge2delta_task >> wait_for_merge2delta >> spark_adding_uuidv7_task >> wait_for_adding_uuidv7 >> [spark_generate_silver_schema_task, spark_generate_data_mart_task]
    # spark_raw2delta_avro_task >> wait_for_raw2delta_avro >> spark_merge2delta_task >> wait_for_merge2delta >> spark_adding_uuidv7_task >> wait_for_adding_uuidv7 >> spark_generate_data_mart_task
    # spark_generate_data_mart_task >> wait_for_generate_data_mart