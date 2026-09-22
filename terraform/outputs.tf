output "namespace" {
  value = kubernetes_namespace_v1.ns.metadata[0].name
}

output "service_name" {
  value = kubernetes_service_v1.app.metadata[0].name
}

output "app_url" {
  value = "http://localhost:${var.node_port}"
}
