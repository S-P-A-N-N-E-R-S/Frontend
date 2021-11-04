from ..network.protocol.build.status_pb2 import StatusType
from .exceptions import NetworkClientError
from . import parserManager


class JobState():
    def __init__(self, jobState):
        self.jobId = jobState.job_id
        self.status = jobState.status
        self.statusMessage = jobState.statusMessage
        self.requestType = jobState.requestType
        self.handlerType = jobState.handlerType
        self.jobName = jobState.jobName

    def getJobName(self):
        if self.jobName:
            return self.jobName
        if self.handlerType:
            handler = parserManager.getRequestParser(self.handlerType)
            handlerName = handler.name
            return f"{handlerName} {self.jobId}"
        return str(self.jobId)

    def isSuccessful(self):
        return self.status == StatusType.SUCCESS


jobStates = {}


def getJobState(jobId):
    try:
        return jobStates[jobId]
    except KeyError as error:
        raise NetworkClientError("Found no job with the given id") from error


def getJobStates():
    return jobStates


def getJobStateDict():
    jobStatesDict = {}
    for jobId, state in jobStates.items():
        jobStatesDict[jobId] = {
            'status': state.status
        }
    return jobStatesDict


def insertJobStates(states):
    for jobState in states:
        jobStates[jobState.job_id] = JobState(jobState)