#  This file is part of the S.P.A.N.N.E.R.S. plugin.
#
#  Copyright (C) 2022  Leon Nienhüser
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, see
#  https://www.gnu.org/licenses/gpl-2.0.html.


from datetime import datetime

from . import handlerManager
from .exceptions import NetworkClientError
from ..network.protocol.build.status_pb2 import StatusType

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
    """Class that contains information about the state of a job"""

    def __init__(self, jobState):
        """
        Constructor

        :param jobState: Job state to be saved
        :type jobState: protobuf message object
        """

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
        """
        Returns a datetime object from the specified timestamp

        :param timestamp: Timestamp to be converted
        :return: Datetime object if valid or None
        """

        if timestamp.seconds > 0:
            return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos/1e9)
        return None

    @property
    def name(self):
        """
        Returns the job's display name; Can be used as a job state sorting option

        :return: Job display name
        """
        return self.getJobName()

    def getJobName(self):
        """
        Returns the job's display name

        :return: Job display name
        """

        if self.jobName:
            return self.jobName
        if self.handlerType:
            handler = handlerManager.getRequestHandler(self.handlerType)
            handlerName = handler.name
            return f"{handlerName} {self.jobId}"
        return str(self.jobId)

    def isRunning(self):
        """
        Returns whether or not the job is still running

        :return: Boolean describing if the job is still running
        """

        return self.status == StatusType.RUNNING or self.status == StatusType.WAITING

    def isSuccessful(self):
        """
        Returns whether or not the job was successful

        :return: Boolean describing if the job was successful
        """

        return self.status == StatusType.SUCCESS

    def getStatus(self):
        """
        Returns the status of the job

        :return: Job status
        """

        return STATUS_TEXTS.get(self.status, STATUS_TEXTS[StatusType.UNKNOWN_STATUS])

    def getStatusText(self):
        """
        Returns human readable status information about the jobs, containing
        multiple timestamps, runtime, error and status messages and the job status

        :return: Human readable status information
        """

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
        """
        Returns the icon name of the icon to be displayed alongside the job status

        :return: The icon name for the job status
        """

        if self.isSuccessful():
            return "SP_DialogApplyButton"
        elif self.isRunning():
            return "SP_DriveHDIcon"
        return "SP_DialogCancelButton"


jobStates = {}


def getJobState(jobId):
    """
    Returns the JobState of the job with the specified job ID

    :param jobId: ID of the desired JobState
    :raises NetworkClientError: If the job ID is unknown
    :return: A JobState with the specified ID
    """

    try:
        return jobStates[jobId]
    except KeyError as error:
        raise NetworkClientError("Found no job with the given id") from error


def jobSortingFunction(job, sortingOption):
    """
    Returns the attribute specified by the sorting option from the specified job

    :param job: JobState object
    :param sortingOption: Attribute name to be fetched
    :return: Job attribute
    """

    return getattr(job, SORTING_OPTIONS.get(sortingOption, "startingTime"))


def getSortedJobStates(sortingOption, sortingDirection):
    """
    Returns all JobStates sorted by the specified sorting option in
    the specified direction

    :param sortingOption: Sorting option
    :param sortingDirection: Sorting direction
    :return: Sorted JobStates
    """

    sortedJobStates = list(jobStates.values())
    sortedJobStates.sort(key= lambda job: jobSortingFunction(job, sortingOption),
        reverse=bool(sortingDirection=="Descending"))
    return sortedJobStates or []


def getJobStates():
    """
    Returns a dictionairy containing all JobStates
    with an unspecified sorting applied

    :return: Dictionairy containing all JobStates
    """

    return jobStates


def getJobStateDict():
    """
    Returns a dictionairy containing all job states
    with an unspecified sorting applied

    :return: Dictionairy containing all job states
    """

    jobStatesDict = {}
    for jobId, state in jobStates.items():
        jobStatesDict[jobId] = {
            'status': state.status
        }
    return jobStatesDict


def getSortingOptions():
    """
    Returns a list of all available sorting options

    :return: All available sorting options
    """

    return list(SORTING_OPTIONS.keys())


def insertJobState(jobState):
    """
    Inserts a new job state to be saved

    :param jobState: Job state to be saved
    :type jobState: Protobuf message object
    """

    jobStates[jobState.job_id] = JobState(jobState)


def insertJobStates(states):
    """
    Inserts multiple new job states to be saved; Deletes currently saved
    job states before inserting the specified job states

    :param jobState: Job states to be saved
    :type jobState: Protobuf message objects
    """

    jobStates.clear()
    for jobState in states:
        jobStates[jobState.job_id] = JobState(jobState)
