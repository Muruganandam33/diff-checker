
# Diff Checker – Beginner DevOps Project

## 1. Objective

Build a complete DevOps pipeline for a Flask-based Diff Checker application.

The project demonstrates:

- Docker containerization
- Headless browser testing using Playwright
- Ansible configuration management
- Terraform infrastructure deployment
- K3s Kubernetes deployment
- Jenkins CI/CD automation

---

## 2. Project Flow

```text
Developer
    |
    v
VS Code
    |
    v
Flask Application
    |
    v
Docker
    |
    v
Playwright Tests
    |
    v
Jenkins Pipeline
    |
    +----> Ansible
    |       |
    |       v
    |    Configuration
    |
    +----> Docker Build
    |
    +----> Playwright Tests
    |
    +----> Terraform
            |
            v
           K3s
            |
            v
     Diff Checker Application
