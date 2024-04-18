#! /usr/bin/env python3

from __future__ import print_function
import sys
from optparse import OptionParser
import random

# to make Python2 and Python3 act the same -- how dumb
def random_seed(seed):
    try:
        random.seed(seed, version=1)
    except:
        random.seed(seed)
    return

parser = OptionParser()
parser.add_option("-s", "--seed", default=0, help="the random seed", action="store", type="int", dest="seed")
parser.add_option("-j", "--jobs", default=3, help="number of jobs in the system", action="store", type="int", dest="jobs")
parser.add_option("-l", "--jlist", default="", help="instead of random jobs, provide a comma-separated list of run times", action="store", type="string", dest="jlist")
parser.add_option("-m", "--maxlen", default=10, help="max length of job", action="store", type="int", dest="maxlen")
parser.add_option("-p", "--policy", default="FIFO", help="sched policy to use: SJF, FIFO, RR", action="store", type="string", dest="policy")
parser.add_option("-q", "--quantum", help="length of time slice for RR policy", default=1, action="store", type="int", dest="quantum")
parser.add_option("-c", help="compute answers for me", action="store_true", default=False, dest="solve")
# add arrival time option
parser.add_option("-a", "--arrival", help="arrival time for each job", default="", action="store", type="string", dest="arrival")
(options, args) = parser.parse_args()

random_seed(options.seed)

print('ARG policy', options.policy)
if options.jlist == '':
    print('ARG jobs', options.jobs)
    # print arrival time
    print('ARG arrival', options.arrival)
    print('ARG maxlen', options.maxlen)
    print('ARG seed', options.seed)
else:
    print('ARG jlist', options.jlist)
print('')

# Set arrival times list
# It will be added to joblist's 2nd element.
jobarrival = []
if options.arrival == '':
    jobarrival = [0] * options.jobs
else:
    jobarrival = list(map(int, options.arrival.split(',')))
if len(jobarrival) != options.jobs:
    print("Error: number of jobs is not equal to number of arrival times")
    exit(0)

print('Here is the job list, with the run time of each job: ')

import operator

joblist = []
if options.jlist == '':
    for jobnum in range(0,options.jobs):
        runtime = int(options.maxlen * random.random()) + 1
        joblist.append([jobnum, runtime, jobarrival[jobnum]])
        print('  Job', jobnum, '( length = ' + str(runtime) + ' / arrival time =', jobarrival[jobnum], ')')
else:
    jobnum = 0
    for runtime in options.jlist.split(','):
        joblist.append([jobnum, float(runtime), jobarrival[jobnum]])
        jobnum += 1
    for job in joblist:
        print('  Job', job[0], '( length = ' + str(job[1]) + ' / arrival time =', job[2], ' )')
print('\n')

if options.solve == True:
    print('** Solutions **\n')

    # Sort joblist by arrival time
    newjoblist = sorted(joblist, key=operator.itemgetter(2))

    if options.policy == 'SJF':
        for j in newjoblist:
            if j[2] == 0:
                newjoblist = sorted(newjoblist, key=operator.itemgetter(1))
                options.policy = 'FIFO'
                break
        # STCF
        if options.policy != 'FIFO':
            runlist = []
            thetime = 0
            runlist.append(newjoblist.pop(0))
            while len(newjoblist) > 0:
                # Add to runlist when arrival time matches
                if newjoblist[0][2] <= thetime:
                    newjoblist = sorted(newjoblist, key=operator.itemgetter(1))
                    runlist.append(newjoblist.pop(0))
                thetime += runlist[0][1]
            newjoblist = runlist
            options.policy = 'FIFO'

    if options.policy == 'FIFO':
        thetime = 0
        print('Execution trace:')
        for job in newjoblist:
            # Calculate CPU idle time
            idletime = max(0, job[2] - thetime)
            if idletime > 0:
                print('  [ time %3d ] CPU idle for %.2f secs' % (thetime, idletime))
            thetime += idletime

            print('  [ time %3d ] Run job %d for %.2f secs ( DONE at %.2f )' % (thetime, job[0], job[1], thetime + job[1]))
            thetime += job[1]

        print('\nFinal statistics:')
        t     = 0.0
        count = 0
        turnaroundSum = 0.0
        waitSum       = 0.0
        responseSum   = 0.0
        info = []
        for tmp in newjoblist:
            # Update CPU idle time
            t += max(0, tmp[2] - t)

            jobnum  = tmp[0]
            runtime = tmp[1]
            arrivaltime = tmp[2]

            response   = max(0, t - arrivaltime)        # firstrun - arrival
            turnaround = (t + runtime) - arrivaltime    # completion - arrival
            wait       = max(0, t - arrivaltime)        # current - arrival

            info.append([jobnum, response, turnaround, wait])
            responseSum   += response
            turnaroundSum += turnaround
            waitSum       += wait
            t += runtime
            count = count + 1

        info.sort(key=operator.itemgetter(0))
        for tmp in info:
            print('  Job %3d -- Response: %3.2f  Turnaround %3.2f  Wait %3.2f' % (tmp[0], tmp[1], tmp[2], tmp[3]))
        print('\n  Average -- Response: %3.2f  Turnaround %3.2f  Wait %3.2f\n' % (responseSum/count, turnaroundSum/count, waitSum/count))
                     
    if options.policy == 'RR':
        print('Execution trace:')
        turnaround = {}
        response = {}
        lastran = {}
        wait = {}
        quantum  = float(options.quantum)
        jobcount = len(newjoblist)
        for i in range(0,jobcount):
            lastran[i] = joblist[i][2]
            wait[i] = 0.0
            turnaround[i] = 0.0
            response[i] = -1

        runlist = []

        thetime  = 0.0
        while jobcount > 0:
            # Add to runlist when arrival time matches
            if len(newjoblist) > 0:
                if newjoblist[0][2] <= thetime:
                    runlist.append(newjoblist.pop(0))
            if len(runlist) == 0:
                print('  [ time %3d ] CPU idle for 1.00 secs' % thetime)
                thetime += 1
                continue
            job = runlist.pop(0)
            jobnum  = job[0]
            runtime = float(job[1])
            if response[jobnum] == -1:
                response[jobnum] = thetime - job[2]                     # firstrun - arrival
            currwait = max(0, thetime - lastran[jobnum])                # current - arrival
            wait[jobnum] += currwait
            if runtime > quantum:
                runtime -= quantum
                ranfor = quantum
                print('  [ time %3d ] Run job %3d for %.2f secs' % (thetime, jobnum, ranfor))
                runlist.append([jobnum, runtime, job[2]])
            else:
                ranfor = runtime
                print('  [ time %3d ] Run job %3d for %.2f secs ( DONE at %.2f )' % (thetime, jobnum, ranfor, thetime + ranfor))
                turnaround[jobnum] = thetime - job[2]                   # completion - arrival
                jobcount -= 1
            thetime += ranfor
            lastran[jobnum] = thetime

        print('\nFinal statistics:')
        turnaroundSum = 0.0
        waitSum       = 0.0
        responseSum   = 0.0
        for i in range(0, len(joblist)):
            turnaroundSum += turnaround[i]
            responseSum += response[i]
            waitSum += wait[i]
            print('  Job %3d -- Response: %3.2f  Turnaround %3.2f  Wait %3.2f' % (i, response[i], turnaround[i], wait[i]))
        count = len(joblist)

        print('\n  Average -- Response: %3.2f  Turnaround %3.2f  Wait %3.2f\n' % (responseSum/count, turnaroundSum/count, waitSum/count))

    if options.policy != 'FIFO' and options.policy != 'SJF' and options.policy != 'RR': 
        print('Error: Policy', options.policy, 'is not available.')
        sys.exit(0)
else:
    print('Compute the turnaround time, response time, and wait time for each job.')
    print('When you are done, run this program again, with the same arguments,')
    print('but with -c, which will thus provide you with the answers. You can use')
    print('-s <somenumber> or your own job list (-l 10,15,20 for example)')
    print('to generate different problems for yourself.')
    print('')
