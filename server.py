import grpc
from concurrent import futures
import lender_pb2, lender_pb2_grpc
import traceback

class LenderService(lender_pb2_grpc.LenderServicer):
    def DbToHdfs(self, request, context):
        return lender_pb2.DbToHdfsResp(error="not implemented")

    def BlockLocations(self, request, context):
        return lender_pb2.BlockLocationsResp(error="not implemented")

    def CalcAvgLoan(self, request, context):
        return lender_pb2.CalcAvgLoanResp(error="not implemented")

print("start server")
server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
lender_pb2_grpc.add_LenderServicer_to_server(LenderService(), server)
server.add_insecure_port("0.0.0.0:5000")
server.start()
server.wait_for_termination()
