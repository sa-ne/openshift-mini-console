# OpenShift Mini Console

OpenShift Mini Console (OMC) is a small Flask application that queries some basic information about an OpenShift cluster using the Python Kubernetes API module.

![Screen Shot](/doc/interface.jpg)

## Fake API Endpoints

In addition to the web interface, you can make `curl` calls to get cluster information as well.

- /infrastructure/name
- /infrastructure/platform
- /infrastructure/region
- /machinesets
- /nodes
- /clusterversion
- /clusterversion/channel
- /clusterversion/id
- /console

## Running OMC Locally

To run the application, clone this git repository on your workstation and run the following commands in the repository folder.

### Create Python Virtual Environment

First we will create a Python virtual environment to use for the application.

```console
python -m venv env
```

Next, activate the virtual environment as follows:

```console
source env/bin/activate
```

### Install OMC Required Python Modules in Virtual Environment

OMC requires the Flask and Kubernetes Python modules, so upgrade pip and install the modules as follows:

```console
python -m pip install --upgrade pip
python -m pip install flask
python -m pip install kubernetes
```
### Starting OMC

Since we are running OMC locally, we need to export the KUBECONFIG environment variable.

```console
export KUBECONFIG=/path/to/kubeconfig
```

Finally, start the Flask application by running:

```console
$ python -m flask run
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

You should now be able to access the application by pointing your browser to http://localhost:5000.

## Running OMC on OpenShift via BuildConfig/Deployment

The `deploy/buildconfig` directory contains all the manifests required to build and deploy OMC on OpenShift. Simply clone this git repository and run the following command to apply the manifests:

```console
oc apply -k deploy/buildconfig
```