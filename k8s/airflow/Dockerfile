FROM apache/airflow:2.10.0

RUN pip install apache-airflow-providers-cncf-kubernetes==10.5.0
RUN pip install apache-airflow-providers-standard==1.2.0

COPY ./dags/ ${AIRFLOW_HOME}/dags/