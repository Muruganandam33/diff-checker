variable "kubeconfig_path" {
  description = "Path to the K3s kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  type    = string
  default = "diff-checker"
}

variable "image" {
  description = "Docker image (must already be imported into K3s)"
  type        = string
  default     = "diff-checker-app:1.0"
}

variable "replicas" {
  type    = number
  default = 1
}

variable "node_port" {
  type    = number
  default = 30081
}

variable "app_env" {
  type    = string
  default = "k3s"
}

variable "app_message" {
  type    = string
  default = "Diff Checker"
}

variable "app_version" {
  type    = string
  default = "1.0"
}
