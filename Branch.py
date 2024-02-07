import grpc
from threading import Thread
from example_pb2 import responseData
from multiprocessing import Process,Value,Lock
import threading
from time import sleep  
import example_pb2_grpc





class Branch(example_pb2_grpc.BankTransactionsServiceServicer):
    
    shared_lock = Lock()
    def __init__(self, id, balance, branches,workerThreads,canQuery):
        # unique ID of the Branch
        self.id = id
        # replica of the Branch's balance
        self.balance = balance
        # the list of process IDs of the branches
        self.branches = branches
        # the list of Client stubs to communicate with the branches
        self.stubList = list()
        self.canQuery = canQuery
        for branch in self.branches:
            _id = int(branch[len(branch) - 2 :])
            if _id == self.id:
                continue
            channel = grpc.insecure_channel(f'localhost:{branch}')
            stub = example_pb2_grpc.BankTransactionsServiceStub(channel)
            self.stubList.append(stub)
        # a list of received messages used for debugging purpose
        self.workerThreadsCount = workerThreads
        self.recvMsg = list()
        # iterate the processID of the branches

        # TODO: students are expected to store the processID of the branches
    def __reduce__(self):
        return (self.__class__,(self.id,self.balance,self.branches,self.workerThreadsCount,self.canQuery))
    
    def Query(self):
        while True:
            if self.canQuery.value == 1:
                break
        return self.balance

    def propogate(self,stub,request):
        stub.MsgDelivery(request)
        with threading.Lock():
            self.workerThreadsCount.value -= 1
    def Withdraw(self,request):
        threads = []
        for stub in self.stubList:
            request.event.interface = "branch/withdraw"
            threads.append(Thread(target=self.propogate,args=(stub,request,)))
        for thread in threads:
            thread.start()
    def Deposit(self,request):
        threads = []
        for stub in self.stubList:
            request.event.interface = "branch/deposit"
            threads.append(Thread(target=self.propogate,args=(stub,request,)))
        for thread in threads:
            thread.start()
    def Propogate_Withdraw(self,amount):
        self.balance -= amount 
        return "success" #return success
        
    def Propogate_Deposit(self,amount):
        self.balance += amount
        return "success" #return success - the status of the request

    def checkThreadsCompletion(self):
        while True:
            if self.workerThreadsCount.value == 0:
                break
            sleep(0.1)
        with threading.Lock():
            self.canQuery.value = 1
            self.workerThreadsCount.value = len(self.stubList)

    # TODO: students are expected to process requests from both Client and Branch
    def MsgDelivery(self,request, context):
        event = request.event
        response = None
        eventType = event.interface
        if eventType == "withdraw":
            self.balance -= request.event.money
            with threading.Lock():
                self.canQuery.value = 0
            response = self.Withdraw(request)
            monitorThread = Thread(target = self.checkThreadsCompletion,args=())
            monitorThread.start()
            return responseData(interface = eventType,branch = self.id,result = "success")
        elif eventType == "deposit":
            self.balance += request.event.money
            with threading.Lock():
                self.canQuery.value = 0
            self.Deposit(request)
            monitorThread = Thread(target = self.checkThreadsCompletion,args=())
            monitorThread.start()
            return responseData(interface = eventType,branch = self.id,result = "success")
        elif eventType == "query":
            response = self.Query()
        else:
            propogateDirection = eventType.split('/')[1]
            if propogateDirection == "withdraw":
                response = self.Propogate_Withdraw(event.money)
                return responseData(interface= eventType,result = response)
            else:
                response = self.Propogate_Deposit(event.money)
                return responseData(interface= eventType,result = response)
        if response is not None:
            return responseData(interface = eventType,branch = self.id,balance = response)
        return responseData(interface = eventType,branch = self.id,result = "success")
        