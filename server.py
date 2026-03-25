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

class LenderService(lender_pb2_grpc.LenderServicer):
    def DbToHdfs(self, request, context):
        for i in range(10):
            try:
                password = "acid"
                conn_str = f"mysql+mysqlconnector://root:{password}@mysql:3306/CS544"
                engine = create_engine(conn_str)
                with engine.connect() as conn:
                    # Connection successful
                    return lender_pb2.DbToHdfsResp(error="connected")

            except (OperationalError, KeyError) as e:
                print(f"Could not connect to MySQL: {e}", file=sys.stderr)
                if i < 9:
                    print("Retrying in 5 seconds...", file=sys.stderr)
                    time.sleep(5)
            except Exception as e:
                traceback.print_exc()
                return lender_pb2.DbToHdfsResp(error=str(e))
        
        return lender_pb2.DbToHdfsResp(error="could not connect to mysql")

    def BlockLocations(self, request, context):
        return lender_pb2.BlockLocationsResp(block_entries={})

    def CalcAvgLoan(self, request, context):
        return lender_pb2.CalcAvgLoanResp(avg_loan=0, source="create")

print("start server")
server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
lender_pb2_grpc.add_LenderServicer_to_server(LenderService(), server)
server.add_insecure_port("0.0.0.0:5000")
server.start()
server.wait_for_termination()
