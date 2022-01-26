from datetime import datetime

from ..network.protocol.build.status_pb2 import StatusType
from .exceptions import NetworkClientError
from . import parserManager

STATUS_TEXTS = {
    StatusType.UNKNOWN_STATUS: "unknown",
    StatusType.WAITING: "waiting",
    StatusType.RUNNING: "running",
    StatusType.SUCCESS: "success",
    StatusType.FAILED: "failed",
    StatusType.ABORTED: "aborted",
}


SORTING_OPTIONS = {
    "Start Time": "startingTime",
    "End Time": "endTime",
    "Runtime": "ogdfRuntime",
    "Status": "status",
    "Name": "name"
}


class JobState():
    def __init__(self, jobState):
        self.jobId = jobState.job_id
        self.status = jobState.status
        self.statusMessage = jobState.statusMessage
        self.requestType = jobState.requestType
        self.handlerType = jobState.handlerType
        self.jobName = jobState.jobName

        self.ogdfRuntime = jobState.ogdfRuntime
        self.timeReceived = self.parseTimestamp(jobState.timeReceived)
        self.startingTime = self.parseTimestamp(jobState.startingTime)
        self.endTime = self.parseTimestamp(jobState.endTime)

    def parseTimestamp(self, timestamp):
        if timestamp.seconds > 0:
            return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos/1e9)
        return None

    @property
    def name(self):
        return self.getJobName()

    def getJobName(self):
        if self.jobName:
            return self.jobName
        if self.handlerType:
            handler = parserManager.getRequestParser(self.handlerType)
            handlerName = handler.name
            return f"{handlerName} {self.jobId}"
        return str(self.jobId)

    def isRunning(self):
        return self.status == StatusType.RUNNING or self.status == StatusType.WAITING

    def isSuccessful(self):
        return self.status == StatusType.SUCCESS

    def getStatus(self):
        return STATUS_TEXTS.get(self.status, STATUS_TEXTS[StatusType.UNKNOWN_STATUS])

    def getStatusText(self):
        status = self.getStatus()
        statusText = f"Status: {status}"

        if self.timeReceived:
            statusText = f"{statusText}\nReceived: {self.timeReceived}"
        if self.startingTime:
            statusText = f"{statusText}\nStarted: {self.startingTime}"
        if not self.isRunning():
            if self.ogdfRuntime > 0:
                statusText = f"{statusText}\nOGDF Runtime: {self.ogdfRuntime} us"
            if self.endTime:
                statusText = f"{statusText}\nEnded: {self.endTime}"

        if self.statusMessage:
            statusText = f"{statusText}\nMessage: {self.statusMessage}"
        elif not self.isRunning() and not self.isSuccessful():
            statusText = f"{statusText}\nMessage: unknown"
        return statusText

    def getIconName(self):
        if self.isSuccessful():
            return "SP_DialogApplyButton"
        elif self.isRunning():
            return "SP_DriveHDIcon"
        return "SP_DialogCancelButton"


jobStates = {}


def getJobState(jobId):
    try:
        return jobStates[jobId]
    except KeyError as error:
        raise NetworkClientError("Found no job with the given id") from error


def jobSortingFunction(job, sortingOption):
    return getattr(job, SORTING_OPTIONS.get(sortingOption, "startingTime"))


def getSortedJobStates(sortingOption, sortingDirection):
    sortedJobStates = list(jobStates.values())
    sortedJobStates.sort(key= lambda job: jobSortingFunction(job, sortingOption),
        reverse=bool(sortingDirection=="Descending"))
    return sortedJobStates or []


def getJobStates():
    return jobStates


def getJobStateDict():
    jobStatesDict = {}
    for jobId, state in jobStates.items():
        jobStatesDict[jobId] = {
            'status': state.status
        }
    return jobStatesDict


def getSortingOptions():
    return list(SORTING_OPTIONS.keys())


def insertJobState(jobState):
    jobStates[jobState.job_id] = JobState(jobState)


def insertJobStates(states):
    jobStates.clear()
    for jobState in states:
        jobStates[jobState.job_id] = JobState(jobState)
