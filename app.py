import os
import socket
import sys
from base64 import b64decode
from threading import active_count
from flask import Flask, render_template, url_for, request
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import obj_minio
import random

app = Flask(__name__)

secret_name = "omc-config"
s3_client = None
cluster_list = []
create_object = True
selected_cluster = ""
omc_config_secret = None
endpoint = ""
region = ""
bucket_name = ""
access_key = ""
secret_key = ""
namespace = ""

if "KUBECONFIG" in os.environ:
    config.load_kube_config()
else:
    config.incluster_config.load_incluster_config()

if os.getenv("IN_CLUSTER", None) is None:
    namespace = os.getenv("namespace", "omc-app")
else:
    namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

crd = client.CustomObjectsApi()
k8s = client.CoreV1Api()

try:
    omc_config_secret = k8s.read_namespaced_secret(secret_name, namespace)
except ApiException as e:
    print("Exception when calling CoreV1Api->read_namespaced_secret: %s\n" % e)

endpoint = b64decode(omc_config_secret.data["endpoint"]).decode("utf-8")
region = b64decode(omc_config_secret.data["region"]).decode("utf-8")
bucket_name = b64decode(omc_config_secret.data["bucket_name"]).decode("utf-8")
access_key = b64decode(omc_config_secret.data["access_key"]).decode("utf-8")
secret_key = b64decode(omc_config_secret.data["secret_key"]).decode("utf-8")


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


def addtestdata(sclient, sbucket_name, test_val):
    '''Method is to simulate adding other clusters with test data'''

    cluster_info = {"name": test_val,
                    "platform": test_val,
                    "region": test_val,
                    "machineset_list": test_val,
                    "node_list": test_val,
                    "version": test_val,
                    "channel": test_val,
                    "clusterid": test_val,
                    "consoleroute": test_val,
                    "pod_hostname": test_val,
                    "pod_ipaddress": test_val}

    result = obj_minio.put_objects_binary(
        client=sclient, bucket_name=sbucket_name,
        object_name=test_val, cluster_info=cluster_info)
    print("created {0} object; etag: {1}, version-id: {2}".format(
        result.object_name, result.etag, result.version_id,),)


@app.route("/", methods=['GET', 'POST'])
def home():
    global s3_client
    global selected_cluster
    global create_object
    cluster_name = None

    try:
        cluster_name = request.form['cluster_name']
    except KeyError:
        pass
    cluster_info = {"name": infrastructure_name(),
                    "platform": infrastructure_platform(),
                    "region": infrastructure_region(),
                    "machineset_list": machinesets_list(),
                    "node_list": nodes_list(),
                    "version": clusterversion_version(),
                    "channel": clusterversion_channel(),
                    "clusterid": clusterversion_clusterid(),
                    "consoleroute": console_route(),
                    "pod_hostname": pod_hostname(),
                    "pod_ipaddress": pod_ipaddress()
                    }

    if cluster_name is None:
        cluster_name = cluster_info["name"]

    if create_object:
        # Create s3_client if does not exist
        if s3_client is None:
            s3_client = obj_minio.create_client(
                endpoint=endpoint, access_key=access_key, secret_key=secret_key, region=region)

        # Check if bucket exists,create if not create
        obj_minio.create_bucket_ifnotexists(s3_client, bucket_name)

        # Put Our Data in Bucket
        result = obj_minio.put_objects_binary(
            s3_client, bucket_name, cluster_info["name"], cluster_info)
        print("created {0} object; etag: {1}, version-id: {2}".format(
            result.object_name, result.etag, result.version_id,),)

        ################ TEST FUNCTION ####################
        # Create test data to test logic only at first load
        # for i in range(1, 10):
        #     addtestdata(s3_client, bucket_name, "test{}".format(i))

    # Get All Objects from bucket
    bucket_objects = obj_minio.get_all_objects_python(
        s3_client, bucket_name)

    ################ TEST FUNCTION ####################
    # Uncomment to test data to test logic on every call
    # addtestdata(s3_client, bucket_name, ''.join(
    #    random.choice('abcdefdfdfafgklkflf') for _ in range(4)))

    if bucket_objects is not None:
        cluster_list = []
        for obj in bucket_objects:
            # Get list of all Cluster Names
            cluster_list.append(obj["name"])

            # Check if we need to add details for this cluster
            if cluster_info["name"] == obj["name"]:
                create_object = False

            # Get info of the presently selected cluster on the page
            if obj["name"] == cluster_name:
                selected_cluster = obj

    # Return details as requested by webpage
    return render_template(
        "index.html",
        name=selected_cluster["name"],
        platform=selected_cluster["platform"],
        region=selected_cluster["region"],
        machineset_list=selected_cluster["machineset_list"],
        node_list=selected_cluster["node_list"],
        version=selected_cluster["version"],
        channel=selected_cluster["channel"],
        clusterid=selected_cluster["clusterid"],
        consoleroute=selected_cluster["consoleroute"],
        pod_hostname=selected_cluster["pod_hostname"],
        pod_ipaddress=selected_cluster["pod_ipaddress"],
        cluster_list=cluster_list
    )

    # # Return only details of the cluster we are running on since we just stored it in s3 above
    # return render_template(
    #     "index.html",
    #     name=infrastructure_name(),
    #     platform=infrastructure_platform(),
    #     region=infrastructure_region(),
    #     machineset_list=machinesets_list(),
    #     node_list=nodes_list(),
    #     version=clusterversion_version(),
    #     channel=clusterversion_channel(),
    #     clusterid=clusterversion_clusterid(),
    #     consoleroute=console_route(),
    #     pod_hostname=pod_hostname(),
    #     pod_ipaddress=pod_ipaddress(),
    #     cluster_list=[infrastructure_name()]
    # )


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
        if hasattr(platform_status[infrastructure_platform().lower()], 'region'):
            return platform_status[infrastructure_platform().lower()]["region"]
        else:
            return "n/a"
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
    if hasattr(clusterversion["spec"], 'channel'):
        return clusterversion["spec"]["channel"]

    return "The update channel has not been configured."


@app.route("/clusterversion/id")
def clusterversion_clusterid():
    return clusterversion["spec"]["clusterID"]


@app.route("/console")
def console_route():
    return consoleroute["spec"]["host"]
