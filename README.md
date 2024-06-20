# Overview
Kubernetes Secrets with Akeyless

## Understanding Kubernetes Secret Types

### Opaque

Opaque is the default Secret type in Kubernetes, used to store arbitrary user-defined data as key-value pairs. 

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: opaque-secret
type: Opaque
data:
  username: YWRtaW4=  # base64 encoded value of 'admin'
  password: czNjcjN0  # base64 encoded value of 's3cr3t'
```

### Bootstrap Token

Bootstrap Tokens are used for cluster bootstrapping and allow new nodes to join the cluster securely.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bootstrap-token
type: bootstrap.kubernetes.io/token
data:
  token-id: dGVzdC10b2tlbg==  # base64 encoded value of 'test-token'
  token-secret: c2VjcmV0  # base64 encoded value of 'secret'
```

### TLS

TLS Secrets store a certificate and its associated key, which are commonly used for HTTPS communication.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1...LS0tLS0K  # base64 encoded certificate
  tls.key: LS0tLS1...LS0tLS0K  # base64 encoded key
```

### SSH Authentication

SSH Authentication Secrets store SSH keys for authentication purposes.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ssh-auth-secret
type: kubernetes.io/ssh-auth
data:
  ssh-privatekey: LS0tLS1...LS0tLS0K  # base64 encoded SSH private key
```

### ImagePullSecrets

ImagePullSecrets store Docker registry credentials used to pull images from private registries.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: image-pull-secret
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: ewogICJhdXRocyI6IHsKICAgICJ...  # base64 encoded Docker config JSON
```

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

With Kustomize, you can generate Secrets dynamically:

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

## Practical Use Cases of Kubernetes Secrets

### Use Secrets to Pull Docker Images from Private Docker Registries

To pull images from a private Docker registry, create a Docker registry Secret:

```bash
kubectl create secret docker-registry my-registry-secret \
  --docker-server=myregistrydomain.com \
  --docker-username=myusername \
  --docker-password=mypassword \
  --docker-email=myemail@domain.com
```

Reference the ImagePullSecret in your Pod specification:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
  - name: mycontainer
    image: myregistrydomain.com/myimage
  imagePullSecrets:
  - name: my-registry-secret
```

### Using Secret Data as Container Environment Variables and in Volume Mounted Files

Example of using Secrets as environment variables in a Pod:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
  - name: mycontainer
    image: myimage
    env:
    - name: USERNAME
      valueFrom:
        secretKeyRef:
          name: my-secret
          key: username
    - name: PASSWORD
      valueFrom:
        secretKeyRef:
          name: my-secret
          key: password
```

Example of using Secrets as volume-mounted files:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
  - name: mycontainer
    image: myimage
    volumeMounts:
    - name: secret-volume
      mountPath: "/etc/secret-volume"
  volumes:
  - name: secret-volume
    secret:
      secretName: my-secret
```

## The Security Limitations of Kubernetes Secrets

### The Misconception of "Secrets": Base64 Encoding Explained

Base64 encoding is often misunderstood as a form of encryption. In reality, it's just a reversible encoding method. Anyone with access to the encoded data can easily decode it. For instance:

```bash
echo 'YWRtaW4=' | base64 --decode  # Outputs 'admin'
```

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

### Explanation of the `akeyless.io/secrets` Annotation

The `akeyless.io/secrets` annotation specifies the mapping of environment variables in your Kubernetes Pod to the secrets stored in Akeyless. Here’s a detailed explanation:

```yaml
akeyless.io/secrets: |
  username=demo-secret:username
  password=demo-secret:password
```

- **`akeyless.io/secrets`**: This annotation is used by the Akeyless Secrets Injector to identify which secrets should be injected into the Pod.
- **`username=demo-secret:username`**: This part of the annotation maps the environment variable `username` in the Pod to the `username` key in the Akeyless secret named `demo-secret`.
  - `username`: The name of the environment variable in the Pod.
  - `demo-secret`: The name of the secret stored in Akeyless.
  - `username`: The specific key within the `demo-secret`

 that holds the desired value.
- **`password=demo-secret:password`**: Similarly, this part maps the environment variable `password` in the Pod to the `password` key in the Akeyless secret named `demo-secret`.
  - `password`: The name of the environment variable in the Pod.
  - `demo-secret`: The name of the secret stored in Akeyless.
  - `password`: The specific key within the `demo-secret` that holds the desired value.

When a Pod with this annotation is created, the Akeyless Secrets Injector webhook intercepts the Pod creation request. It then:
1. **Fetches the Secret**: Retrieves the specified secrets (`demo-secret`) from Akeyless.
2. **Extracts Values**: Extracts the values of the specified keys (`username` and `password`) from the Akeyless secret.
3. **Injects Environment Variables**: Injects these values as environment variables (`username` and `password`) into the Pod's container.

### External Secrets Operator

The External Secrets Operator allows you to sync secrets from Akeyless to Kubernetes Secrets. Deploy the External Secrets Operator in your cluster and create an ExternalSecret resource:

```yaml
apiVersion: external-secrets.io/v1alpha1
kind: ExternalSecret
metadata:
  name: my-external-secret
spec:
  backendType: akeyless
  data:
    - key: /path/to/secret
      name: my-secret
  target:
    name: my-k8s-secret
```

### K8s Secrets Store CSI Driver

The K8s Secrets Store CSI Driver enables you to mount Akeyless secrets directly into your pods as files. Install the CSI driver in your cluster and create a SecretProviderClass resource:

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: akeyless-secrets
spec:
  provider: akeyless
  parameters:
    objects: |
      array:
        - objectName: "my-secret"
          objectType: "secret"
```

Then, reference the SecretProviderClass in your Pod specification:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
  - name: mycontainer
    image: myimage
    volumeMounts:
    - name: secrets-store
      mountPath: "/mnt/secrets-store"
      readOnly: true
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: "akeyless-secrets"
```

### Using Akeyless with Annotations to Enforce Specific Rules for Secret Management

Akeyless allows you to enforce specific rules for secret management using Kubernetes annotations. This ensures that secrets are managed according to your organization's security policies.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
  annotations:
    akeyless.io/secret: "my-secret"
spec:
  containers:
  - name: mycontainer
    image: myimage
```

## Demo: Using Akeyless with Kubernetes Secrets

In this demo, we'll walk through the process of integrating Akeyless with Kubernetes to manage secrets securely using the Akeyless agent injector.

### Prerequisites

- Kubernetes cluster
- Akeyless account and API key
- kubectl installed

### Step 1: Install Akeyless Secrets Injector

First, install the Akeyless Secrets Injector in your Kubernetes cluster. The injector will automatically inject secrets into your Kubernetes pods at runtime.

```bash
kubectl apply -f https://raw.githubusercontent.com/akeylesslabs/akeyless-k8s-injector/main/deploy.yaml
```

### Step 2: Configure Akeyless Secrets

Log in to your Akeyless account and create a secret. For this demo, let's create a secret called `demo-secret` with a username and password.

1. Navigate to the Akeyless console.
2. Create a new secret under your vault, named `demo-secret`.
3. Add key-value pairs to the secret:
   - `username`: `admin`
   - `password`: `s3cr3t`

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
