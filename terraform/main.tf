resource "kubernetes_namespace_v1" "ns" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_config_map_v1" "config" {
  metadata {
    name      = "diff-checker-config"
    namespace = kubernetes_namespace_v1.ns.metadata[0].name
  }

  data = {
    APP_ENV     = var.app_env
    APP_MESSAGE = var.app_message
    APP_VERSION = var.app_version
  }
}

resource "kubernetes_deployment_v1" "app" {
  metadata {
    name      = "diff-checker"
    namespace = kubernetes_namespace_v1.ns.metadata[0].name
    labels = {
      app = "diff-checker"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = "diff-checker"
      }
    }

    template {
      metadata {
        labels = {
          app = "diff-checker"
        }
      }

      spec {
        container {
          name              = "diff-checker"
          image             = var.image
          image_pull_policy = "IfNotPresent"

          port {
            container_port = 5000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.config.metadata[0].name
            }
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 5000
            }
            initial_delay_seconds = 3
            period_seconds        = 5
          }
        }
      }
    }
  }

  # Fail after 3 minutes instead of waiting forever (e.g. ImagePullBackOff)
  timeouts {
    create = "3m"
    update = "3m"
  }
}

resource "kubernetes_service_v1" "app" {
  metadata {
    name      = "diff-checker"
    namespace = kubernetes_namespace_v1.ns.metadata[0].name
  }

  spec {
    type = "NodePort"

    selector = {
      app = "diff-checker"
    }

    port {
      port        = 80
      target_port = 5000
      node_port   = var.node_port
    }
  }
}
