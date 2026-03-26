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
                    query = """
                        SELECT l.*
                        FROM loans l
                        INNER JOIN loan_types t
                            ON l.loan_type_id = t.id
                        WHERE t.loan_type_name = 'Conventional'
                        LIMIT 10
                    """
                    df = pd.read_sql(query, conn)
                    row_count = len(df)

                    os.environ["CLASSPATH"] = subprocess.check_output(
                        ["hadoop", "classpath", "--glob"], text=True
                    ).strip()

                    fs = pa.fs.HadoopFileSystem(
                        host="nn",                     # IMPORTANT: service name
                        port=9000,
                        user="root",
                        replication=2,                 # required
                        default_block_size=1024 * 1024 # 1 MB
                    )

                    table = pa.Table.from_pandas(df)

                    pq.write_table(
                        table,
                        "hdfs://nn:9000/hdma-wi-2021.parquet",
                        filesystem=fs,
                        compression="snappy"
                    )

                    return lender_pb2.DbToHdfsResp(error="", row_count=row_count)
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
server = grpc.server(futures.ThreadPoolExecutor(max_workers=8), options=[("grpc.so_reuseport", 0)])
lender_pb2_grpc.add_LenderServicer_to_server(LenderService(), server)
port = server.add_insecure_port("[::]:5000")
print(f"Bound to port: {port}", flush=True)
server.start()
print("gRPC server listening on port 5000...", flush=True)
server.wait_for_termination()
