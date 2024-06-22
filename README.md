# Overview
Kubernetes Secrets with Akeyless

## Creating and Managing Kubernetes Secrets

### Creating Secrets Using kubectl

To create a Secret using `kubectl`, you can use the following command:

```bash
kubectl create secret generic my-secret --from-literal=username=admin --from-literal=password='s3cr3t'
```

You can verify the Secret was created successfully with:

```bash
kubectl get secret my-secret
```

### Using a Manifest File and Generators Like Kustomize

You can also create Secrets using a YAML file:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
type: Opaque
data:
  username: YWRtaW4=  # base64 encoded value of 'admin'
  password: czNjcjN0  # base64 encoded value of 's3cr3t'
```

Apply the Secret using `kubectl`:

```bash
kubectl apply -f my-secret.yaml
```

With Kustomize, you can generate Secrets dynamically with a `kustomization.yaml` file:

```yaml
secretGenerator:
- name: my-secret
  literals:
  - username=admin
  - password=s3cr3t
```

Run the following command to apply the Kustomize configuration:

```bash
kubectl apply -k .
```
## The Security Limitations of Kubernetes Secrets

### The Misconception of "Secrets": Base64 Encoding Explained

Base64 encoding is often misunderstood as a form of encryption. In reality, it's just a reversible encoding method. Anyone with access to the encoded data can easily decode it. For instance:

```bash
echo 'YWRtaW4=' | base64 --decode  # Outputs 'admin'
```

We can easily get the secret from the database, in our case we're using a k3s cluster with SQLite

```bash
sqlite3 /var/lib/rancher/k3s/server/db/state.db
```

Then run the following SQL command:

```sql
SELECT name, hex(value) FROM kine WHERE name LIKE '%secrets%opaque-secret%';
```

Finally take that 
## Integrating Akeyless with Kubernetes Environments

### Akeyless Secrets Injector

The Akeyless Secrets Injector automatically injects secrets into your applications at runtime. This eliminates the need to store secrets in your application code or configuration files.

To use the Akeyless Secrets Injector, deploy the Akeyless Injector webhook in your Kubernetes cluster. Configure your Pod annotations to specify which secrets to inject:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
  annotations:
    akeyless.io/inject: "true"
    akeyless.io/secrets: |
      username=demo-secret:username
      password=demo-secret:password
spec:
  containers:
  - name: mycontainer
    image: nginx
    env:
    - name: USERNAME
      value: $(username)
    - name: PASSWORD
      value: $(password)
```

## Using Akeyless with Kubernetes Secrets

In this demo, we'll walk through the process of integrating Akeyless with Kubernetes to manage secrets securely using the Akeyless agent injector. You can find more [details in the docs.](https://docs.akeyless.io/docs/how-to-provision-secret-to-your-k8s)

### Prerequisites

- Kubernetes cluster v1.19 and above
- Helm and kubectl installed
- Akeyless account
- [K8s Authentication Method Configured](https://docs.akeyless.io/docs/dedicated-k8s-auth-service-accounts)

### Step 1: Install Akeyless Secrets Injector

First, install the Akeyless Secrets Injector in your Kubernetes cluster. The injector will automatically inject secrets into your Kubernetes pods at runtime.

```bash
helm repo add akeyless https://akeylesslabs.github.io/helm-charts
helm repo update
```


There are two modes for K8s secrets.  Envar and file injection.  The drawback with Envar mode is you require a restart of the pod if the secret changes

### Step 2: Configure Akeyless Secrets

Log in to your Akeyless account and create a static secret. 

### Step 3: Annotate Your Kubernetes Pod for Secret Injection

Deploy a Pod and configure it to use the Akeyless secret by adding annotations to the Pod specification. This tells the Akeyless injector which secrets to inject.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo-pod
  annotations:
    akeyless.io/inject: "true"
    akeyless.io/secrets: |
      username=demo-secret:username
      password=demo-secret:password
spec:
  containers:
  - name: demo-container
    image: nginx
    env:
    - name: USERNAME
      value: $(username)
    - name: PASSWORD
      value: $(password)
```

### Step 4: Deploy the Pod

Apply the Pod configuration to your Kubernetes cluster:

```bash
kubectl apply -f demo-pod.yaml
```

### Step 5: Verify the Pod

Check the environment variables in the Pod to ensure the secrets were injected correctly. You can do this by running a command inside the Pod:

```bash
kubectl exec demo-pod -- env
```

Look for the `USERNAME` and `PASSWORD` environment variables in the output. They should have the values `admin` and `s3cr3t`, respectively.

### Detailed Explanation

1. **Annotations**: The `akeyless.io/inject: "true"` annotation enables secret injection for the Pod. The `akeyless.io/secrets` annotation specifies which Akeyless secrets to inject and the corresponding environment variable names.

2. **Injector Deployment**: The Akeyless Secrets Injector is deployed as a Kubernetes admission webhook that intercepts Pod creation requests and injects the specified secrets into the Pod.

3. **Secret Management**: By using Akeyless, you centralize secret management and avoid storing sensitive information directly in your Kubernetes manifests or etcd.
