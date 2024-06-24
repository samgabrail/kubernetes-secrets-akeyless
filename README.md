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
helm upgrade --install aks akeyless/akeyless-secrets-injection --namespace akeyless -f values.yaml
```

Notice the `values.yaml` file contains the following environment variables:
```yaml
env:
  AKEYLESS_URL: "https://vault.akeyless.io"
  AKEYLESS_ACCESS_ID: "p-ukwx42wczc5skm" 
  AKEYLESS_ACCESS_TYPE: "k8s"
  AKEYLESS_API_GW_URL: "https://b46b-24-150-170-114.ngrok-free.app"
  AKEYLESS_K8S_AUTH_CONF_NAME: "my-k8s-auth-method"
```

- `AKEYLESS_ACCESS_ID` is the Access ID of the Auth Method with access to the secret.
- `AKEYLESS_ACCESS_TYPE` is k8s since we're using the Kubernetes authentication method.
- `AKEYLESS_K8S_AUTH_CONF_NAME` is set to our Gateway Kubernetes Auth name. Relevant only for Access type of k8s.
- `AKEYLESS_API_GW_URL` is set with the URL of my Akeyless Gateway on port 8080. Since my gateway is running on my local machine, I'm using ngrok with `ngrok http 8080` to forward an external url of `https://b46b-24-150-170-114.ngrok-free.app` to `http://localhost:8080`. This allows communication between my apps running in K8s and the gateway.

#### Modes of Retrieval of Secrets in Akeyless
There are two modes to retrieve secrets with Akeyless in K8s. Environment variables and file injection. The drawback with environment variables mode is you require a restart of the pod if the secret changes. With file injection, the secret is written to a file in the pod. You can use a sidecar to continously retrieve updates to secrets in Akeyless. This is helpful for rotated and dynamic secrets.

### Step 2: Retrieve Secrets into Environment Variables

Let's now retrieve a secret from Akeyless into an environment variable. Run the following command:

```bash
kubectl apply -f app_env.yaml
```

Notice the content of this file:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-environment-variable
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hello-secrets
  template:
    metadata:
      labels:
        app: hello-secrets
      annotations:
        akeyless/enabled: "true"
    spec:
      containers:
      - name: alpine
        image: alpine
        command:
          - "sh"
          - "-c"
          - "echo $MY_SECRET && echo ...going to sleep... && sleep 10000"
        env:
        - name: MY_SECRET
          value: akeyless:/K8s/my_k8s_secret
```

Notice the following annotation:

- akeyless/enabled: "true": An annotation that enables the K8s Injector plugin.

Now check the logs of the pod:

Output:
```
Defaulted container "alpine" out of: alpine, akeyless-init (init)
myPassword
...going to sleep...
```

It successfully retrieved the password in Akeyless: `myPassword`

### Step 3: Retrieve Secrets into a File

Let's now retrieve a secret from Akeyless into a file. Run the following command:

```bash
kubectl apply -f app_file.yaml
```

Here are the contents of the `app_file.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-file
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hello-secrets-2
  template:
    metadata:
      labels:
        app: hello-secrets-2
      annotations:
        akeyless/enabled: "true"
        akeyless/inject_file: "/K8s/my_k8s_secret"
    spec:
      containers:
      - name: alpine
        image: alpine
        command:
          - "sh"
          - "-c"
          - "cat /akeyless/secrets/K8s/my_k8s_secret && echo ...going to sleep... && sleep 2000"
```

Notice the following annotations:

- akeyless/enabled: "true": An annotation that enables the K8s Injector plugin
- akeyless/inject_file: "/K8s/my_k8s_secret": An annotation specifying the path to get the secret from in Akeyless. The default location of the Akeyless secrets folder inside your pod file system is `/akeyless/secrets/`. To explicitly set a different location you can override this by adding `|location=<path>` after your secret name within the annotation as we will see in the next example.

Check the logs of this pod:

Output:

```
Defaulted container "alpine" out of: alpine, akeyless-init (init)
myPassword
```

We got the same output as before. However, let's exec into the container and look at the file where the secret was written into. Run this command:

```bash
kubectl exec -it pod/test-file-b9b6d4699-gprjf -c alpine -- sh
cat /akeyless/secrets/K8s/my_k8s_secret 
```

The content of the file will have the same password we saw earlier: `myPassword`.

This is great if our application is intended to retrieve the secret once from Akeyless, so an akeyless-init container retrieving the secret then exiting is appropriate. However, there are times where we need to continuously retrieve secrets from Akeyless. In this case, a sidecar container is needed. Let's see how to do that in the next example.

### Step 4: Retrieve Secrets into a File Continously with a Sidecar

Let's now retrieve a secret from Akeyless into a file continously with a sidecar. Run the following command:

```bash
kubectl apply -f app_file_sidecar.yaml
```

and here are the contents of the `app_file_sidecar.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-file-sidecar
spec:
  replicas: 1
  selector:
    matchLabels:
      app: file-secrets
  template:
    metadata:
      labels:
        app: file-secrets
      annotations:
        akeyless/enabled: "true"
        akeyless/inject_file: "/K8s/my_k8s_secret|location=/secrets/secretsVersion.json" 
        akeyless/side_car_enabled: "true"
        akeyless/side_car_refresh_interval: "5s"
        akeyless/side_car_versions_to_retrieve: "2"
    spec:
      containers:
      - name: alpine
        image: alpine
        command:
          - "sh"
          - "-c"
          - "while true; do [ ! -f /secrets/timestamp ] || [ /secrets/secretsVersion.json -nt /secrets/timestamp ] && touch /secrets/timestamp && cat /secrets/secretsVersion.json && echo ''; sleep 15; done"
```

Notice the following annotations:

- akeyless/enabled: "true" -> An annotation that enables the K8s Injector plugin
- akeyless/inject_file: "/K8s/my_k8s_secret|location=/secrets/secretsVersion.json" -> An annotation specifying the path to get the secret from in Akeyless. Here we're specifying where to write the secret in the pod's file system at `/secrets/secretsVersion.json`.
- akeyless/side_car_enabled: "true" -> This is what enables the sidecar container.
- akeyless/side_car_refresh_interval: "5s" -> This specifies the interval at which the sidecar will check for new versions of the secret.
- akeyless/side_car_versions_to_retrieve: "2" -> This specifies the number of versions of the secret to retrieve.

If you run `kubectl get po`, you will see that we have now two containers running for our pod:

```bash
NAME                                         READY   STATUS    RESTARTS      AGE
test-file-sidecar-759667cccc-6h8xv           2/2     Running   0             43m
```

Now check the logs of the `akeyless-sidecar` container:

```bash
kubectl logs -f po/test-file-sidecar-759667cccc-6h8xv -c akeyless-sidecar
```

Output:

```bash
2024/06/22 14:58:02 [INFO] Secret /K8s/my_k8s_secret was successfully written to: /secrets/secretsVersion.json
```

and check the logs of the `alpine` container:

```bash
kubectl logs -f po/test-file-sidecar-759667cccc-6h8xv -c alpine
```

Output:

```json
{
  "version": 1,
  "secret_value": "myPassword",
  "creation_date": 1719068280
}
```

Now update the secret in the Akeyless UI:

and notice the logs will automatically change to reflect the new secret:
```json
[
 {
  "version": 2,
  "secret_value": "myPassword2",
  "creation_date": 1719071019
 },
 {
  "version": 1,
  "secret_value": "myPassword",
  "creation_date": 1719068280
 }
]
```
Finally, we can exec into the alpine container to see the file where all the secrets live:

```bash
kubectl exec -it pod/test-file-sidecar-759667cccc-6h8xv -c alpine -- sh
cat /secrets/secretsVersion.json 
```

Output:

```json
[
 {
  "version": 2,
  "secret_value": "myPassword2",
  "creation_date": 1719071019
 },
 {
  "version": 1,
  "secret_value": "myPassword",
  "creation_date": 1719068280
 }
]
```

As we just saw, we are now able to actively retrieve new versions of the secret and write them to the file system. Now the application developers need to build some logic into their applications to read the file and use the secret with retry mechanisms in case of failures due to an expired secret. This is the direction organizations should take to reduce long-lived credentials in their environments.