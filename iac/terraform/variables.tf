variable "project_id" {
    description = "The project ID to host the cluster"
    default     = "tokyo-dream-461703-i3"
}

variable "cluster_name" {
    description = "The name of the cluster"
    default     = "amazonreviews-standard-cluster"
}

variable "filestore_name" {
    description = "The name of the filestore"
    default     = "amazonreviews-filestore"
}

variable "filestore_tier" {
    description = "The type of tier storage"
    default     = "BASIC_HDD"
}

variable "region" {
    description = "The region of the cluster in"
    default     = "asia-southeast1"
}

variable "zone" {
    description = "The zone the cluster in"
    default     = "asia-southeast1-a"
}