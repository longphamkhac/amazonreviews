# Stream Processing Setup

## Description
This project sets up a stream processing environment using Kubernetes namespaces, Postgres, MinIO for storage, and Helm for deployment. It creates buckets for Apache Flink and Kafka tiered storage, enabling scalable data processing pipelines.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Verification](#verification)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites
- **Kubernetes CLI (`kubectl`)**: Ensure `kubectl` is installed and configured to interact with your cluster.
- **Helm**: Version 3.x for deploying the storage chart.
- **MinIO Client (`mc`)**: For managing MinIO buckets.
- **Configuration Files**:
  - `config/postgres/postgres-credentials.properties`
  - `config/s3/access-key.properties`
  - `config/s3/secret-key.properties`
- A running Kubernetes cluster with sufficient resources.

## Installation
Follow these steps to set up the stream processing environment.

### 1. Create Kubernetes Namespaces
Create namespaces for infrastructure, processor, and airflow.

```shell
kubectl create namespace infrastructure
kubectl create namespace processor
kubectl create namespace airflow
```

### 2. Install Postgres and MinIO Credentials
Create Kubernetes secrets for Postgres and MinIO credentials in the specified namespaces.

```shell
kubectl create secret generic postgres-credentials \
  --from-file=config/postgres/postgres-credentials.properties \
  -n infrastructure

kubectl create secret generic minio-credentials \
  --from-file=access-key=config/s3/access-key.properties \
  --from-file=secret-key=config/s3/secret-key.properties \
  -n infrastructure

kubectl create secret generic minio-credentials \
  --from-file=access-key=config/s3/access-key.properties \
  --from-file=secret-key=config/s3/secret-key.properties \
  -n processor
```

### 3. Install Storage (Postgres and MinIO)
Deploy Postgres and MinIO using the Helm chart in the `infrastructure` namespace.

```shell
helm upgrade --install storage helm/storage -n infrastructure
```

### 4. Create MinIO Buckets
Set up the MinIO alias and create buckets for Flink and Kafka tiered storage.

```shell
mc alias set minio http://minio-svc:9000 minio_access_key minio_secret_key
mc mb minio/flink-data
mc mb minio/kafka-tiered-storage
```

**Note**: Replace `minio_access_key` and `minio_secret_key` with the actual values from your `config/s3/` files.

## Usage
Once the setup is complete, the environment is ready for stream processing tasks:
- **Postgres**: Use for structured data storage and querying.
- **MinIO**: Access the `flink-data` and `kafka-tiered-storage` buckets for data storage and retrieval.
- **Namespaces**: Deploy Flink, Kafka, or Airflow workloads in the respective namespaces (`processor`, `airflow`).

Ensure your applications are configured to use the secrets (`postgres-credentials`, `minio-credentials`) for authentication.

## Verification
Verify the MinIO buckets were created successfully.

```shell
mc ls minio
```

This command lists all buckets in the MinIO instance, confirming `flink-data` and `kafka-tiered-storage` are present.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

Please ensure your changes are compatible with the Kubernetes and Helm versions specified in [Prerequisites](#prerequisites).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.