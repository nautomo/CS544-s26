from concurrent import futures

import grpc
import pandas as pd
import property_pb2
import property_pb2_grpc


class DatasetServer(property_pb2_grpc.PropertyLookupServicer):
    def __init__(self, csv_path):
        df = pd.read_csv(
            csv_path, usecols=["Parcel", "Address"], dtype=str, compression="gzip"
        )
        df.dropna(inplace=True)
        self.parcel_index = (
            df.groupby("Parcel")["Address"]
            .apply(lambda addr: sorted(addr.tolist()))
            .to_dict()
        )

    def addressByParcel(self, request, context):
        parcel = request.parcel
        addresses = self.parcel_index.get(parcel, [])
        return property_pb2.AddressResponse(address=addresses)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    service = DatasetServer("/data/addresses.csv.gz")
    property_pb2_grpc.add_PropertyLookupServicer_to_server(service, server)
    server.add_insecure_port("[::]:5000")
    server.start()
    print("Server started on port 5000")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
