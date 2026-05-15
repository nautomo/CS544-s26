import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;
import property.Property.ParcelRequest;
import property.Property.AddressResponse;
import property.PropertyLookupGrpc;

import java.io.*;
import java.util.*;
import java.util.zip.GZIPInputStream;

public class DatasetServer extends PropertyLookupGrpc.PropertyLookupImplBase {
    // parcel string -> sorted list of addresses
    private final Map<String, SortedSet<String>> parcelIndex = new HashMap<>();

    public DatasetServer(String csvPath) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new GZIPInputStream(new FileInputStream(csvPath))))) {
            String headerLine = reader.readLine();
            List<String> headers = Arrays.asList(headerLine.split(","));
            int parcelIdx = headers.indexOf("Parcel");
            int addressIdx = headers.indexOf("Address");

            String line;
            while ((line = reader.readLine()) != null) {
                String[] fields = line.split(",", -1);
                if (fields.length <= Math.max(parcelIdx, addressIdx)) continue;

                String address = fields[addressIdx];
                if (address == null || address.isEmpty()) continue;

                String parcel = fields[parcelIdx];
                if (parcel != null && !parcel.isEmpty()) {
                    parcelIndex.computeIfAbsent(parcel, k -> new TreeSet<>()).add(address);
                }
            }
        }
        System.out.println("Loaded " + parcelIndex.size() + " parcels");
    }

    @Override
    public void addressByParcel(ParcelRequest request, StreamObserver<AddressResponse> responseObserver) {
        String parcel = request.getParcel();
        SortedSet<String> addrs = parcelIndex.getOrDefault(parcel, null);
        AddressResponse.Builder builder = AddressResponse.newBuilder();
        if (addrs == null || addrs.isEmpty()) {
            builder.setError("no addresses found");
        } else {
            builder.addAllAddresses(addrs);
        }
        AddressResponse response = builder.build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }


    public static void main(String[] args) throws Exception {
        DatasetServer service = new DatasetServer("/data/addresses.csv.gz");
        Server server = ServerBuilder.forPort(5000)
                .addService(service)
                .executor(java.util.concurrent.Executors.newFixedThreadPool(16))
                .build()
                .start();
        System.out.println("Server started on port 5000");
        server.awaitTermination();
    }
}
