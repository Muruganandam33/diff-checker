# Diff Checker – Beginner DevOps Project

## 1. Objective
Jenkins pipeline that runs **headless browser tests inside Docker**, uses **Ansible** to manage the config file, and deploys to **K3s** using **Terraform**. Everything runs locally on Windows + WSL2 + Ubuntu, from the VS Code terminal.

## 2. Flow
```
Developer → VS Code → Flask app → Docker → Playwright tests (in Docker)
          → Jenkins → Ansible (config) → Terraform → K3s → Running app
```
| Tool | Role |
|---|---|
| Flask | The web app (compare two texts) |
| Docker | Packs the app (and the tests) into containers |
| Playwright | Opens the app in a headless Chromium and checks it works |
| Jenkins | Automates build → test → deploy |
| Ansible | Generates the config file `config/app.env` |
| K3s | Small Kubernetes running locally |
| Kubernetes | Runs and exposes the container (Deployment, Service, ConfigMap) |
| Terraform | Creates the Kubernetes resources from code |

## 3. Folder structure
```
diff-checker/
├── app/            app.py, templates/index.html, static/style.css
├── tests/          test_diff_checker.py
├── docker/         Dockerfile.app, Dockerfile.tests
├── ansible/        inventory.ini, playbook.yml, vars/main.yml, templates/app.env.j2
├── k8s/            namespace, configmap, deployment, service (.yaml)
├── terraform/      providers.tf, variables.tf, main.tf, outputs.tf
├── Jenkinsfile, requirements.txt, requirements-test.txt, .dockerignore, .gitignore, README.md
```
Names used everywhere: images `diff-checker-app:1.0`, `diff-checker-tests:1.0` · container `diff-checker-app` · network `diffnet` · namespace `diff-checker` · NodePort `30080` · Flask port `5000`.

## 4. Prerequisites
Windows 10/11 with WSL2 + Ubuntu 22.04/24.04, VS Code with the **WSL** extension, Docker Desktop (Settings → Resources → WSL Integration → enable your Ubuntu). Internet access.

---

# STEP-BY-STEP (run in this exact order)

## STEP 1 – Open the project in VS Code
📁 Run in: Ubuntu terminal, any folder
```bash
cd ~/diff-checker
code .
```
Puts you in VS Code connected to WSL (bottom-left shows `WSL: Ubuntu`).
> If you have the zip: `sudo apt install -y unzip && cd ~ && unzip /mnt/c/Users/<WindowsUser>/Downloads/diff-checker.zip`

## STEP 2 – Open Ubuntu terminal in VS Code
Menu **Terminal → New Terminal**. The prompt should look like `user@PC:~/diff-checker$`.

## STEP 3 – Verify Linux
📁 `~/diff-checker`
```bash
uname -a
```
Expected: contains `Linux ... microsoft-standard-WSL2`.

## STEP 4 – Verify Python
📁 `~/diff-checker`
```bash
python3 --version
sudo apt update && sudo apt install -y python3-venv python3-pip curl
```
Expected: `Python 3.10+`.

## STEP 5 – Verify Docker
📁 `~/diff-checker`
```bash
docker --version
docker ps
```
Expected: version line, then an (empty) table `CONTAINER ID IMAGE ...`.
Errors → see Troubleshooting 1 and 2.

## STEP 6 – Install Python dependencies
📁 `~/diff-checker`
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Creates a private Python environment and installs Flask.

## STEP 7 – Run Flask locally
📁 `~/diff-checker`
```bash
python3 app/app.py
```
Expected: `Running on http://127.0.0.1:5000`. Leave it running.

## STEP 8 – Open in browser
Windows browser: **http://localhost:5000**. Type `Hello World` / `Hello DevOps`, click **Compare**.
Second terminal: `curl http://localhost:5000/health` → `{"status":"ok","version":"1.0"}`.
**Stop Flask with Ctrl+C** (Docker needs port 5000 next).

## STEP 9 – Build Flask Docker image
📁 `~/diff-checker`
```bash
docker build -f docker/Dockerfile.app -t diff-checker-app:1.0 .
```
Expected: `naming to docker.io/library/diff-checker-app:1.0`.

## STEP 10 – Run Flask Docker container
📁 `~/diff-checker`
```bash
docker network create diffnet
docker run -d --name diff-checker-app --network diffnet -p 5000:5000 \
  -e APP_ENV=development -e APP_MESSAGE="Diff Checker" -e APP_VERSION=1.0 \
  diff-checker-app:1.0
curl http://localhost:5000/health
```
Creates a shared network (so the test container can reach the app), starts the app. Browser: http://localhost:5000.

## STEP 11 – Build Playwright test image
📁 `~/diff-checker`
```bash
docker build -f docker/Dockerfile.tests -t diff-checker-tests:1.0 .
```
First build downloads ~1.5 GB (Chromium included). Be patient.

## STEP 12 – Run Playwright headless tests inside Docker
📁 `~/diff-checker`
```bash
docker run --rm --ipc=host --network diffnet \
  -e BASE_URL=http://diff-checker-app:5000 diff-checker-tests:1.0
```
Expected: `7 passed`.
Then remove containers:
```bash
docker rm -f diff-checker-app
docker network rm diffnet
```

## STEP 13 – Install Ansible
📁 `~/diff-checker`
```bash
sudo apt install -y ansible
ansible --version
```

## STEP 14 – Run Ansible playbook
📁 `~/diff-checker/ansible`
```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml
cat ../config/app.env
cd ..
```
Expected: `failed=0` and
```
APP_ENV=development
APP_MESSAGE=Diff Checker
APP_VERSION=1.0
```
Try it: edit `ansible/vars/main.yml` (e.g. `app_version: "2.0"`), rerun, and the file updates. Use the file with Docker: `docker run --env-file config/app.env ...`.

## STEP 15 – Install K3s
K3s needs **systemd** in WSL2. Check:
📁 `~/diff-checker`
```bash
ps -p 1 -o comm=
```
If it prints `systemd` → skip to the install command. If it prints `init`:
```bash
sudo nano /etc/wsl.conf      # add these two lines (keep any existing content)
#   [boot]
#   systemd=true
```
Then in **Windows PowerShell** (only Windows command in this project): `wsl --shutdown`. Reopen Ubuntu, run `cd ~/diff-checker && code .`.

Install K3s and give yourself kubectl access:
```bash
curl -sfL https://get.k3s.io | sh -
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
```

## STEP 16 – Verify kubectl and the node
```bash
kubectl get nodes
```
Expected: one node, `STATUS Ready`, `ROLES control-plane,master`.
(Wait 30 s and retry if `NotReady`.)

## STEP 17 – Deploy Kubernetes manifests
📁 `~/diff-checker`

K3s uses containerd, not Docker, so first import the image:
```bash
docker save diff-checker-app:1.0 | sudo k3s ctr images import -
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```
Expected: `namespace/diff-checker created`, `configmap/... created`, `deployment.apps/... created`, `service/... created`.

## STEP 18 – Verify pods and services
```bash
kubectl get pods -n diff-checker
kubectl get services -n diff-checker
kubectl logs -n diff-checker deployment/diff-checker
```
Expected: pod `1/1 Running`; service `diff-checker NodePort ... 80:30080/TCP`.

## STEP 19 – Access the app in K3s
```bash
curl http://localhost:30080/health
```
Browser: **http://localhost:30080** → environment shows `k3s`.
If the browser cannot reach it: `kubectl port-forward -n diff-checker svc/diff-checker 8081:80` then open http://localhost:8081.

## STEP 20 – Install Terraform
📁 `~/diff-checker`
```bash
sudo apt install -y gnupg lsb-release wget
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install -y terraform
terraform version
```

## STEP 21 – Terraform: init, validate, plan, apply
Terraform must own the resources, so delete the manual ones from Step 17 first:
📁 `~/diff-checker`
```bash
kubectl delete namespace diff-checker
```
📁 `~/diff-checker/terraform`
```bash
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
```
Type `yes` when asked. Expected: `Plan: 4 to add` → `Apply complete! Resources: 4 added`, and output `app_url = "http://localhost:30080"`.

## STEP 22 – Verify Terraform-created resources
```bash
kubectl get all,configmap -n diff-checker
terraform output
curl http://localhost:30080/health
```
Change `replicas` in `terraform/variables.tf` to 2, run `terraform apply` again and watch a second pod appear. Clean up when done: `terraform destroy`.

## STEP 23 – Configure Jenkins
I run Jenkins **directly in Ubuntu** (not in a container). It then uses the same Docker, Ansible, Terraform and kubectl you already installed – the simplest setup.

📁 any folder
```bash
sudo apt install -y openjdk-17-jre
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list
sudo apt update && sudo apt install -y jenkins
```
Give Jenkins the access it needs:
```bash
# 1) Docker access
sudo usermod -aG docker jenkins
# 2) kubectl / Terraform access to K3s
sudo mkdir -p /var/lib/jenkins/.kube
sudo cp /etc/rancher/k3s/k3s.yaml /var/lib/jenkins/.kube/config
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube
# 3) allow ONLY the k3s image import command without a password
echo 'jenkins ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images import -' | sudo tee /etc/sudoers.d/jenkins-k3s
sudo chmod 440 /etc/sudoers.d/jenkins-k3s && sudo visudo -c
# 4) let Jenkins read your project folder
chmod o+x /home/$USER
sudo -u jenkins git config --global --add safe.directory /home/$USER/diff-checker
# start
sudo systemctl enable jenkins && sudo systemctl restart jenkins
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```
Open **http://localhost:8080**, paste the password, choose **Install suggested plugins**, create your admin user.
**Minimum plugins:** *Pipeline* and *Git* (both included in suggested plugins). Nothing else.

Quick check that Jenkins has access:
```bash
sudo -u jenkins docker ps
sudo -u jenkins kubectl get nodes
sudo -u jenkins ansible --version
sudo -u jenkins terraform version
```

## STEP 24 – Create the Jenkins pipeline
Jenkins reads the Jenkinsfile from Git, so commit the project first (no GitHub needed):
📁 `~/diff-checker`
```bash
git init -b main
git add .
git commit -m "Diff Checker DevOps project"
git status
```
(If Git asks who you are: `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.)

In Jenkins: **New Item** → name `diff-checker` → **Pipeline** → OK.
- Definition: **Pipeline script from SCM**
- SCM: **Git**, Repository URL: `/home/<your-ubuntu-username>/diff-checker`
- Branch: `*/main`
- Script Path: `Jenkinsfile`
- **Save**

## STEP 25 – Run the Jenkins pipeline
Jenkins keeps its own Terraform state, so remove what Step 21 created:
📁 `~/diff-checker/terraform`
```bash
terraform destroy -auto-approve
```
In Jenkins click **Build Now**, then open the build → **Console Output**.
Expected: all 13 stages green, ending with `Finished: SUCCESS`.

## STEP 26 – Verify final deployment
```bash
kubectl get pods,svc -n diff-checker
curl http://localhost:30080/health
```
Browser: **http://localhost:30080** – the Diff Checker is running in K3s, deployed by Jenkins + Terraform.

---

## Git commands (quick reference)
```bash
git init -b main      # create repo
git add .             # stage all files
git commit -m "msg"   # save a snapshot
git status            # see what changed
```
After changing code: `git add . && git commit -m "change"` before running Jenkins again.

## Clean up everything
```bash
cd ~/diff-checker/terraform && terraform destroy -auto-approve
docker rm -f diff-checker-app; docker network rm diffnet
```

---

# TROUBLESHOOTING

1. **Docker daemon not running** (`Cannot connect to the Docker daemon`) – Start Docker Desktop, wait for the whale icon to be steady. Check Settings → Resources → WSL Integration → Ubuntu is ON. Then `docker ps`.
2. **Permission denied on Docker socket** – `sudo usermod -aG docker $USER`, then close and reopen the terminal (or `newgrp docker`). Quick fix: `sudo chmod 666 /var/run/docker.sock`.
3. **Port 5000 already in use** – Stop local Flask (Ctrl+C) or find it: `sudo ss -ltnp | grep 5000`, then `docker rm -f diff-checker-app` or `kill <PID>`.
4. **Playwright browser errors** – Make sure `--ipc=host` is used and the versions match (`Dockerfile.tests` `v1.47.0` = `playwright==1.47.0`). Rebuild: `docker build --no-cache -f docker/Dockerfile.tests -t diff-checker-tests:1.0 .`. `Application did not start` → the app container is not running: `docker ps`, `docker logs diff-checker-app`, and check `--network diffnet` on both.
5. **Ansible: command not found** – `sudo apt install -y ansible`, reopen terminal.
6. **Ansible permission errors** – The playbook writes to `~/diff-checker/config`. Make sure you own the folder: `sudo chown -R $USER:$USER ~/diff-checker`. For Jenkins the workspace is owned by `jenkins`, so no change is needed.
7. **K3s installation problems** – `ps -p 1 -o comm=` must print `systemd` (see Step 15). Check the service: `sudo systemctl status k3s`, logs: `sudo journalctl -u k3s -n 50`. Restart: `sudo systemctl restart k3s`.
8. **kubectl: command not found / connection refused** – K3s installs kubectl at `/usr/local/bin/kubectl`. If it fails with `localhost:8080 refused`, the kubeconfig is missing: repeat the 3 `mkdir/cp/chown` commands in Step 15. Or `export KUBECONFIG=~/.kube/config`.
9. **CrashLoopBackOff** – `kubectl logs -n diff-checker deployment/diff-checker` and `kubectl describe pod -n diff-checker <pod>`. Usually a wrong image or config name.
10. **ImagePullBackOff / ErrImagePull** – The image is not inside K3s. Run `docker save diff-checker-app:1.0 | sudo k3s ctr images import -`, check with `sudo k3s ctr images ls | grep diff-checker`, then `kubectl rollout restart deployment/diff-checker -n diff-checker`.
11. **Service not accessible** – `kubectl get pods -n diff-checker` (must be `1/1 Running`), `kubectl get svc -n diff-checker` (must show `80:30080`). Try `curl http://localhost:30080/health` inside WSL first. Windows browser fails? Use `kubectl port-forward -n diff-checker svc/diff-checker 8081:80`.
12. **Terraform provider errors** – `terraform init` needs internet (registry.terraform.io). Retry; if it is corrupted: `rm -rf .terraform .terraform.lock.hcl && terraform init`.
13. **Terraform state errors** – `already exists` → the resource was created another way: `kubectl delete namespace diff-checker` then `terraform apply`. State lost/out of sync: delete namespace with kubectl and remove `terraform.tfstate*` files. `Unauthorized/connection refused` → fix kubeconfig (item 8).
14. **Jenkins cannot access Docker** (`permission denied ... docker.sock`) – `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`. Verify: `sudo -u jenkins docker ps`. If still failing: `sudo chmod 666 /var/run/docker.sock`.
15. **Jenkins cannot access kubectl/K3s** – Re-copy kubeconfig to `/var/lib/jenkins/.kube/config` (Step 23 #2). `sudo: a password is required` → redo sudoers line (Step 23 #3); the path must match `which k3s`. After a K3s restart the certificates stay valid, but if you reinstall K3s copy the kubeconfig again.
16. **WSL networking issues** – `localhost` from Windows normally works. If not: `wsl --shutdown` in PowerShell and reopen Ubuntu. No internet in WSL? `cat /etc/resolv.conf`; fix DNS with `sudo nano /etc/wsl.conf` → `[network]` `generateResolvConf=false`, then set `nameserver 8.8.8.8` in `/etc/resolv.conf`. Last resort: use the WSL IP from `hostname -I` instead of `localhost`.

**Jenkins git errors** (`dubious ownership`, `not a git repository`) – Repeat the `safe.directory` and `chmod o+x /home/$USER` commands from Step 23 and make sure you committed (Step 24).
