import flask
from flask import Flask
import grpc
import property_pb2
import property_pb2_grpc
import os

app = Flask("p2")

project = os.environ.get("PROJECT", "p2")
dataset_impl = os.environ.get("DATASET_IMPLEMENTATION", "JAVA").upper()

if dataset_impl == "PYTHON":
    channel1 = grpc.insecure_channel(f"{project}-python-dataset-1:5000")
    channel2 = grpc.insecure_channel(f"{project}-python-dataset-2:5000")
else:
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
    global last_used, cache, cache_order

    if parcel in cache:
        addrs = cache[parcel]
        cache_order.remove(parcel)
        cache_order.append(parcel)
        return flask.jsonify({"source": "cache", "addrs": addrs, "error": ""})

    if last_used == "2":
        first_stub, first_source = stub1, "1"
        second_stub,second_source = stub2, "2"
    else:
        first_stub, first_source = stub2, "2"
        second_stub, second_source = stub1, "1"

    # we get a gRPC response from the server, but the failed flag is True
    try:
        response = first_stub.AddressByParcel(property_pb2.ParcelRequest(parcel=parcel), timeout=1)
        addrs = list(response.addresses)
        error = response.error or ("no addresses found" if not addrs else "")

        if not error:
            cache[parcel] = addrs
            cache_order.append(parcel)
            if len(cache) > cache_size:
                victim = cache_order.pop(0)
                cache.pop(victim)

        last_used = first_source
        return flask.jsonify({"source": first_source, "addrs": addrs, "error": error})
    # the gRPC call produces a gRPC specific exception
    except grpc.RpcError:
        try:
            last_used = second_source
            response = second_stub.AddressByParcel(property_pb2.ParcelRequest(parcel=parcel), timeout=1)
            addrs = list(response.addresses)
            error = response.error or ("no addresses found" if not addrs else "")

            if not error:
                cache[parcel] = addrs
                cache_order.append(parcel)
                if len(cache) > cache_size:
                    victim = cache_order.pop(0)
                    cache.pop(victim)

            last_used = second_source
            return flask.jsonify({"source": second_source, "addrs": addrs, "error": error})
        except grpc.RpcError:
            last_used = second_source
            return flask.jsonify({"source": second_source, "addrs": [], "error": "grpc error"})
    # the gRPC call produces a different kind of exception
    except Exception as e:
        return flask.jsonify({"source": first_source, "addrs": [], "error": str(e)})

@app.route("/zip/<zipcode>")
def zip_lookup(zipcode):
    global last_used, cache, cache_order

    if zipcode in cache:
        addrs = cache[zipcode]
        cache_order.remove(zipcode)
        cache_order.append(zipcode)
        return flask.jsonify({"source": "cache", "addrs": addrs, "error": ""})

    if last_used == "2":
        first_stub, first_source = stub1, "1"
        second_stub,second_source = stub2, "2"
    else:
        first_stub, first_source = stub2, "2"
        second_stub, second_source = stub1, "1"

    # we get a gRPC response from the server, but the failed flag is True
    try:
        response = first_stub.AddressByZip(property_pb2.ZipRequest(zip=zipcode), timeout=1)
        addrs = list(response.addresses)
        error = response.error or ("no addresses found" if not addrs else "")

        if not error:
            cache[zipcode] = addrs
            cache_order.append(zipcode)
            if len(cache) > cache_size:
                victim = cache_order.pop(0)
                cache.pop(victim)

        last_used = first_source
        return flask.jsonify({"source": first_source, "addrs": addrs, "error": error})
    # the gRPC call produces a gRPC specific exception
    except grpc.RpcError:
        try:
            response = second_stub.AddressByZip(property_pb2.ZipRequest(zip=zipcode), timeout=1)
            addrs = list(response.addresses)
            error = response.error or ("no addresses found" if not addrs else "")

            if not error:
                cache[zipcode] = addrs
                cache_order.append(zipcode)
                if len(cache) > cache_size:
                    victim = cache_order.pop(0)
                    cache.pop(victim)

            last_used = second_source
            return flask.jsonify({"source": second_source, "addrs": addrs, "error": error})
        except grpc.RpcError:
            last_used = second_source
            return flask.jsonify({"source": second_source, "addrs": [], "error": "grpc error"})
    # the gRPC call produces a different kind of exception
    except Exception as e:
        return flask.jsonify({"source": first_source, "addrs": [], "error": str(e)})

def main():
    app.run("0.0.0.0", port=5000, debug=False, threaded=False)

if __name__ == "__main__":
    main()
