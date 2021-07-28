import os
import socket
from flask import Flask, render_template
from kubernetes import client, config

app = Flask(__name__)

if "KUBECONFIG" in os.environ:
  config.load_kube_config()
else:
  config.incluster_config.load_incluster_config()

crd = client.CustomObjectsApi()
k8s = client.CoreV1Api()

infrastructure = crd.get_cluster_custom_object(
  "config.openshift.io",
  "v1",
  "infrastructures",
  "cluster"
)

clusterversion = crd.get_cluster_custom_object(
  "config.openshift.io",
  "v1",
  "clusterversions",
  "version"
)

machinesets = crd.list_namespaced_custom_object(
  "machine.openshift.io",
  "v1beta1",
  "openshift-machine-api",
  "machinesets"
)

consoleroute = crd.get_namespaced_custom_object(
  "route.openshift.io",
  "v1",
  "openshift-console",
  "routes",
  "console"
)

nodes = k8s.list_node()

@app.route("/")
def home():
  return render_template(
    "index.html",
    name = infrastructure_name(),
    platform = infrastructure_platform(),
    region = infrastructure_region(),
    machineset_list = machinesets_list(),
    node_list = nodes_list(),
    version = clusterversion_version(),
    channel = clusterversion_channel(),
    clusterid = clusterversion_clusterid(),
    consoleroute = console_route(),
    pod_hostname = pod_hostname(),
    pod_ipaddress = pod_ipaddress()
  )

@app.route("/pod/hostname")
def pod_hostname():
  return socket.gethostname()

@app.route("/pod/ipaddress")
def pod_ipaddress():
  return socket.gethostbyname(pod_hostname())

@app.route("/infrastructure/name")
def infrastructure_name():
  return infrastructure["status"]["infrastructureName"]

@app.route("/infrastructure/platform")
def infrastructure_platform():
  return infrastructure["status"]["platform"]

@app.route("/infrastructure/region")
def infrastructure_region():
  platform_status = infrastructure["status"]["platformStatus"]

  if infrastructure_platform().lower() in platform_status:
    return platform_status[infrastructure_platform().lower()]["region"]
  else:
    return "n/a"

@app.route("/machinesets")
def machinesets_list():
  ret = ""

  if "items" in machinesets:
    for item in machinesets["items"]:
      ret = ret + "\n" + item["metadata"]["name"]

  return "n/a" if (len(ret) == 0) else ret[1:]

@app.route("/nodes")
def nodes_list():
  ret = ""

  for node in nodes.items:
    ret = ret + "\n" + node.metadata.name + " ("

    for label in node.metadata.labels:
      if "node-role.kubernetes.io/" in label:
        ret += label.split("/")[1]
    
    ret += ")"
  
  return "n/a" if (len(ret) == 0) else ret[1:]

@app.route("/clusterversion")
def clusterversion_version():
  return clusterversion["status"]["desired"]["version"]

@app.route("/clusterversion/channel")
def clusterversion_channel():
  return clusterversion["spec"]["channel"]

@app.route("/clusterversion/id")
def clusterversion_clusterid():
  return clusterversion["spec"]["clusterID"]

@app.route("/console")
def console_route():
  return consoleroute["spec"]["host"]