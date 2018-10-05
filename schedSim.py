#!/usr/bin/python3.4

import numpy as np
from sys import argv
import csv

def main():
    algorithm, quantum = checkArgs()
    runTimes, arrivalTimes = readJobs()
    maxClock = getMaxClock(runTimes, arrivalTimes)

    if(algorithm == 'FIFO'):
        turnaroundTimes, waitTimes = simFIFO(runTimes, arrivalTimes, maxClock)
    elif(algorithm == 'SRJN'):
        turnaroundTimes, waitTimes = simSRJN(runTimes, arrivalTimes, maxClock)
    else:
        turnaroundTimes, waitTimes = simRR(runTimes, arrivalTimes, quantum, maxClock)

    avgTT, avgWaitT = calcAvg(turnaroundTimes, waitTimes)

    prettyPrint(turnaroundTimes, waitTimes, avgTT, avgWaitT)

#Obtain algorithm and quantum from commandline args
def checkArgs():
    argc = len(argv)
    algorithm = "FIFO"
    quantum = 1
    #-p and -q are optional

    if ((argc != 2) & (argc != 4) & (argc != 6)):
        print("Usage: python3 schedSim.py <job-file.txt> -p <ALGORITHM> -q <QUANTUM>")
        exit()

    if (argc == 4):
        if(argv[2] == "-p"):
            algorithm = checkAlg(argv[3])
        elif(argv[2] == "-q"):
            quantum = checkQ(argv[3])
        else:
            print("Usage: python3 schedSim.py <job-file.txt> -p <ALGORITHM> -q <QUANTUM>")
            exit()

    elif (argc == 6):
        if((argv[2] == "-p") & (argv[4] == "-q")):
            algorithm = checkAlg(argv[3])
            quantum = checkQ(argv[5])
        elif((argv[2] == "-q") & (argv[4] == "-p")):
            quantum = checkQ(argv[3])
            algorithm = checkAlg(argv[5])
        else:
            print("Usage: python3 schedSim.py <job-file.txt> -p <ALGORITHM> -q <QUANTUM>")
            exit()

    return algorithm, quantum

# Check for valid quantum, else return q = 1
def checkQ(q):
    try:
        quantum = int(q)
        if (quantum < 1):
            quantum = 1
    except(ValueError):
        quantum = 1
    return quantum

# Check for valid Alg, else return Alg = 'FIFO'
def checkAlg(alg):
    if((alg != 'FIFO') & (alg != 'RR') & (alg != 'SRJN')):
        alg = 'FIFO'
    return alg

def readJobs():
    #Read from job-file.txt
    with open(argv[1], 'r') as f:
        jobs = np.asarray([tuple(map(int,line)) \
            for line in csv.reader(f, skipinitialspace=False,delimiter=' ')])

    #Sort jobs by arrival time
    jobs = jobs[jobs[:,1].argsort()]

    runTimes = np.asarray([job[0] for job in jobs])
    arrivalTimes = np.asarray([job[1] for job in jobs])

    return runTimes, arrivalTimes

def getMaxClock(runTimes, arrivalTimes):
    #Clock never needs to tick above the total run time
    totalRunTime = sum(time for time in runTimes)
    lastArrival = max(time for time in arrivalTimes)
    maxClock = totalRunTime + lastArrival
    return maxClock

def simFIFO(runTimes, arrivalTimes, maxClock):
    turnaroundTimes = []
    waitTimes = []
    queue = []
    jobNum = 0

    for t in runTimes:
        queue.append(-1)
        turnaroundTimes.append(0)
        waitTimes.append(0)

    #Clock Loop
    for time in range(0, maxClock):
        #Check for arrival
        for i in range(0, len(arrivalTimes)):
            if(arrivalTimes[i] == time):
                queue[i] = runTimes[i]

        queue[jobNum] -= 1

        if(queue[jobNum] == 0):
            waitTimes[jobNum] = (time+1) - runTimes[jobNum] - arrivalTimes[jobNum]
            turnaroundTimes[jobNum] = (time + 1) - arrivalTimes[jobNum]
            jobNum += 1

        #If all jobs completed
        if(all(t == 0 for t in queue)):
            break
    
    return turnaroundTimes, waitTimes

def simSRJN(runTimes, arrivalTimes, maxClock):
    turnaroundTimes = []
    waitTimes = []

    recievedProc = []

    #Initialize to allow for indexed look up
    for job in arrivalTimes:
        recievedProc.append(-1)
        waitTimes.append(0)
        turnaroundTimes.append(0)

    #Clock loop
    for time in range(0, maxClock):
        # Check for arrival
        for i in range(0, len(arrivalTimes)):
            # If just arrived
            if(arrivalTimes[i] == time):
                recievedProc[i] = runTimes[i]

        if (any(t > 0 for t in recievedProc)):
            # Find shortest job index
            shortestJob = recievedProc.index(min(time1 for time1 in recievedProc if time1 > 0))

            # Do work on job
            recievedProc[shortestJob] -= 1

            # Shortest job completes, calculate stats
            if(recievedProc[shortestJob] == 0):
                waitTimes[shortestJob] = (time+1) - runTimes[shortestJob] - arrivalTimes[shortestJob]
                turnaroundTimes[shortestJob] = (time + 1) - arrivalTimes[shortestJob]

    return turnaroundTimes, waitTimes

def simRR(runTimes, arrivalTimes, quantum, maxClock):
    timeElapsed = 0
    #Used to check if job completed
    flagF = 0

    turnaroundTimes = []
    waitTimes = []

    # Contains tuple conatining (jobNum, time remaining)
    queue = []

    #Initialize to allow for indexed look up
    for job in arrivalTimes:
        waitTimes.append(0)
        turnaroundTimes.append(0)

    for i in range(0, len(arrivalTimes)):
        if (arrivalTimes[i] == 0):
            queue.append([i, runTimes[i]])

    #Clock loop
    for time in range(0, maxClock):
        #If queue contains jobs
        if(len(queue) != 0):
            timeElapsed += 1
            queue[0][1] -= 1

            #Check for job completetion
            if (queue[0][1] == 0):
                waitTimes[queue[0][0]] = (time + 1) - runTimes[queue[0][0]] - arrivalTimes[queue[0][0]]
                turnaroundTimes[queue[0][0]] = (time + 1) - arrivalTimes[queue[0][0]]

                flagF = 1
                queue.pop(0)

            #Quanta completed
            if (quantum == timeElapsed):
                if((len(queue) != 0) & (flagF == 0)):
                    currJob = queue.pop(0)
                    queue.append(currJob)
                flagF = 0
                timeElapsed = 0

        #Check for new jobs
        for i in range(0, len(arrivalTimes)):
            if (arrivalTimes[i] == (time+1)):
                queue.append([i, runTimes[i]])

    return turnaroundTimes, waitTimes

def calcAvg(turnaroundTimes, waitTimes):
    avgTT = sum(tTime for tTime in turnaroundTimes)/len(turnaroundTimes)
    avgWaitT = sum(wTime for wTime in waitTimes)/len(waitTimes)

    return avgTT, avgWaitT

def prettyPrint(turnaroundTimes, waitTimes, avgTT, avgWaitT):
    for i in range(0, len(turnaroundTimes)):
        job = i
        turnAround = turnaroundTimes[i]
        wait = waitTimes[i]
        print('Job %3d -- Turnaround %3.2f  Wait %3.2f' % (job, turnAround, wait))
    print('Average -- Turnaround %3.2f  Wait %3.2f' % (avgTT, avgWaitT))

if __name__ == "__main__":
    main()