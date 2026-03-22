import sys
import grpc
import argparse
from concurrent import futures
import lender_pb2, lender_pb2_grpc


def main():
    parser = argparse.ArgumentParser(description="argument parser for p4 client")
    parser.add_argument("mode", help="which action to take", choices=["DbToHdfs","BlockLocations","CalcAvgLoan"])
    parser.add_argument("-c", "--code", type=int, default=0, help="county code to query average loan amount in CalcAvgLoan mode")
    parser.add_argument("-f", "--file", type=str, default="", help="file path for BlockLocations")
    args = parser.parse_args()

    channel = grpc.insecure_channel("server:5000")
    stub = lender_pb2_grpc.LenderStub(channel)
    if args.mode == "DbToHdfs":
        resp = stub.DbToHdfs(lender_pb2.Empty())
        if resp.error:
            print(f"error: {resp.error}", file=sys.stderr)
            sys.exit(1)
        else:
            print(resp.row_count)
    elif args.mode == "CalcAvgLoan":
        resp = stub.CalcAvgLoan(lender_pb2.CalcAvgLoanReq(county_code=args.code))
        if resp.error:
            print(f"error: {resp.error}", file=sys.stderr)
            sys.exit(1)
        else:
            print(resp.avg_loan)
            print(resp.source)
    elif args.mode == "BlockLocations":
        resp = stub.BlockLocations(lender_pb2.BlockLocationsReq(path=args.file))
        if resp.error:
            print(f"error: {resp.error}", file=sys.stderr)
            sys.exit(1)
        else:
            print(resp.block_entries)


if __name__ == "__main__":
    main()
