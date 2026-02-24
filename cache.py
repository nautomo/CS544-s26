import flask
from flask import Flask
import grpc
import property_pb2
import property_pb2_grpc
import os

app = Flask("p2")

project = os.environ.get("PROJECT", "p2")
channel1 = grpc.insecure_channel(f"{project}-java-dataset-1:5000")
channel2 = grpc.insecure_channel(f"{project}-java-dataset-2:5000")
stub1 = property_pb2_grpc.PropertyLookupStub(channel1)
stub2 = property_pb2_grpc.PropertyLookupStub(channel2)

last_used = "2"

cache = {}
cache_order = []
cache_size = 6

@app.route("/parcelnum/<parcel>")
def parcel_lookup(parcel):
    global last_used
    global cache
    global cache_order
    addrs = []
    error = ""

    if parcel in cache:
        addrs = cache[parcel]
        cache_order.remove(parcel)
        cache_order.append(parcel)
        return flask.jsonify({"source": "cache", "addrs": addrs, "error": ""})

    if last_used == "2":
        first_stub = stub1
        first_source = "1"
        second_stub = stub2
        second_source = "2"
    else:
        first_stub = stub2
        first_source = "2"
        second_stub = stub1
        second_source = "1"

    last_used = first_source

    # we get a gRPC response from the server, but the failed flag is True
    try:
        response = first_stub.AddressByParcel(property_pb2.ParcelRequest(parcel=parcel), timeout=1)
        addrs = list(response.addresses)
        if response.failed:
            error = "unknown backend error"
        else:
            cache[parcel] = addrs
            cache_order.append(parcel)
            if len(cache) > cache_size:
                victim = cache_order.pop(0)
                cache.pop(victim)
        return flask.jsonify({"source": first_source, "addrs": addrs, "error": error})
    # the gRPC call produces a gRPC specific exception
    except grpc.RpcError:
        try:
            last_used = second_source
            response = second_stub.AddressByParcel(property_pb2.ParcelRequest(parcel=parcel), timeout=1)
            addrs = list(response.addresses)
            if response.failed:
                error = "unknown backend error"
            else:
                cache[parcel] = addrs
                cache_order.append(parcel)
                if len(cache) > cache_size:
                    victim = cache_order.pop(0)
                    cache.pop(victim)
            return flask.jsonify({"source": second_source, "addrs": addrs, "error": error})
        except grpc.RpcError:
            return flask.jsonify({"source": second_source, "addrs": [], "error": "grpc error"})
    # the gRPC call produces a different kind of exception
    except Exception as error:
        return flask.jsonify({"source": first_source, "addrs": [], "error": str(error)})

def main():
    app.run("0.0.0.0", port=5000, debug=False, threaded=False)

if __name__ == "__main__":
    main()
