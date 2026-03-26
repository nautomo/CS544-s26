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
                    # Query for loans with "Conventional" type
                    df = pd.read_sql(
                        "SELECT l.* FROM loans l "
                        "INNER JOIN loan_types t ON l.loan_type_id = t.id "
                        "WHERE t.loan_type_name = 'Conventional' LIMIT 10;",
                        conn
                    )
                row_count = len(df)
                break
            except OperationalError as e:
                print(f"MySQL not ready: {e}", file=sys.stderr)
                if attempt < 4:
                    print("Retrying in 5 seconds...", file=sys.stderr)
                    time.sleep(5)
                else:
                    return lender_pb2.DbToHdfsResp(error="Could not connect to MySQL", row_count=0)
            except Exception as e:
                traceback.print_exc()
                return lender_pb2.DbToHdfsResp(error=str(e), row_count=0)

        # --- Set CLASSPATH for PyArrow HDFS ---
        try:
            os.environ["CLASSPATH"] = subprocess.check_output(
                ["hadoop", "classpath", "--glob"], text=True
            ).strip()
        except Exception as e:
            return lender_pb2.DbToHdfsResp(error=f"Failed to set CLASSPATH: {e}", row_count=0)

        # --- Connect to HDFS ---
        try:
            fs = pa.fs.HadoopFileSystem(
                host="nn",
                port=9000,
                user="root",
                replication=2,
                default_block_size=1024 * 1024  # 1 MB
            )
            fs.create_dir("/hdma-wi-2021", recursive=True)

            # Remove existing parquet file if exists
            try:
                fs.delete_file("/hdma-wi-2021/hdma-wi-2021.parquet")
            except FileNotFoundError:
                pass
        except Exception as e:
            traceback.print_exc()
            return lender_pb2.DbToHdfsResp(error=f"HDFS connection or directory failed: {e}", row_count=0)

        # --- Convert DataFrame to PyArrow Table and write to HDFS ---
        try:
            table = pa.Table.from_pandas(df)
            pq.write_table(
                table,
                "/hdma-wi-2021/hdma-wi-2021.parquet",
                filesystem=fs,
                compression="snappy",
                coerce_timestamps="ms"
            )
        except Exception as e:
            traceback.print_exc()
            return lender_pb2.DbToHdfsResp(error=f"Failed to write Parquet to HDFS: {e}", row_count=0)

        return lender_pb2.DbToHdfsResp(error="", row_count=row_count)

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
