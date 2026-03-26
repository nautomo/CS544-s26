import grpc
from concurrent import futures
import lender_pb2, lender_pb2_grpc
import traceback
import time
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import subprocess

class LenderService(lender_pb2_grpc.LenderServicer):
    def DbToHdfs(self, request, context):
        # --- MySQL connection with retries ---
        password = "acid"
        conn_str = f"mysql+mysqlconnector://root:{password}@mysql:3306/CS544"

        for attempt in range(5):
            try:
                engine = create_engine(conn_str)
                with engine.connect() as conn:
                    return lender_pb2.DbToHdfsResp(error="connected")
            except OperationalError as e:
                print(f"MySQL not ready: {e}", file=sys.stderr)
                if attempt < 4:
                    print("Retrying in 5 seconds...", file=sys.stderr)
                    time.sleep(5)
            except Exception as e:
                traceback.print_exc()
                return lender_pb2.DbToHdfsResp(error=str(e), row_count=0)
        
        return lender_pb2.DbToHdfsResp(error="Could not connect to MySQL", row_count=0)

    def BlockLocations(self, request, context):
        return lender_pb2.BlockLocationsResp(error="not implemented")

    def CalcAvgLoan(self, request, context):
        return lender_pb2.CalcAvgLoanResp(error="not implemented")

print("start server")
server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
lender_pb2_grpc.add_LenderServicer_to_server(LenderService(), server)
server.add_insecure_port("0.0.0.0:5000")
server.start()
print("gRPC server listening on port 5000...", flush=True)
server.wait_for_termination()
