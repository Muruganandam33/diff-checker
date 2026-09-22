terraform {
  required_version = ">= 1.3.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
  }
}

# Connect to K3s using the kubeconfig file (copied to ~/.kube/config)
provider "kubernetes" {
  config_path = var.kubeconfig_path
}
