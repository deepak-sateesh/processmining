from IPython.core.display import HTML
from flask import Flask, render_template, request, redirect
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.util import sorting
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.organizational_mining.roles import algorithm as roles_discovery
import numpy as np
from pm4py.statistics.eventually_follows.log import get as efg_get
from pm4py.algo.filtering.log import ltl as ll

app = Flask(__name__)
cols = ['Detected Weakness Row', 'Case ID', 'Weakness Type (AF/PA)', 'Weakness ID', 'Weakness Origin', 'Weakness Time',
        'Weakness Information', 'Weakness Measurement', 'Weakness Level']
df = pd.DataFrame(columns=cols)


logSorted = []


# Checks for the largest common prefix
def lcp(s, t):
    n = min(len(s), len(t));
    for i in range(0, n):
        if s[i] != t[i]:
            return s[0:i];
        else:
            return s[0:n];


def Find_sequence(eventList):
    lrs = ""
    n = len(eventList)
    for i in range(0, n):
        for j in range(i + 1, n):
            # Checks for the largest common factors in every substring
            x = lcp(eventList[i:n], eventList[j:n])
            # If the current prefix is greater than previous one
            # then it takes the current one as longest repeating sequence
            if len(x) > len(lrs):
                lrs = x

    if len(set(lrs)) > 1:
        return (lrs)


def Backloop(log):
    print("Backloop function")
    global df
    for case_index, case in enumerate(log):
        eventList = []
        lrs = ""
        indexList = []
        for event_index, event in enumerate(case):
            eventList.append(event["Activity"])
        if Find_sequence(eventList) is not None:
            lrs = Find_sequence(eventList)
            # print("Repeating sequence for events in case:",case.attributes['concept:name']," is: ", lrs)
            row = {cols[0]: event['row_num'], cols[1]: case.attributes['Case ID'], cols[2]: 'AF', cols[3]: '2',
                   cols[4]: 'Automatic detection', cols[5]: '', cols[6]: 'Backloop {' + ''.join(lrs) + '}',
                   cols[7]: 'In the case', cols[8]: 'Process level'}
            df = df.append(row, ignore_index=True)
    # for trace in event_log:
    #    print(trace)


@app.route("/")
@app.route('/<PageName>')
def home(PageName=None):
    global logSorted
    global df
    temp = ""
    columnNames=""
    if (PageName != None):
        if PageName == "backloop":
            PageName = "Backloops"
            df.drop(df.index, inplace=True)
            Backloop(logSorted)
        elif (PageName == "eventuallyFollows"):
            PageName = "Eventually Follows"
        elif (PageName == "parallelizableTasks"):
            PageName = "Parallelizable Tasks"
        elif (PageName == "redundantActivity"):
            PageName = "Redundant Activity"
        elif (PageName == "unwantedActivity"):
            PageName = "Unwanted Activity"

        elif PageName == "bottleNeck":
            PageName = "Bottleneck"
        elif PageName == "idleTime":
            PageName = "Idle Time"
        elif PageName == "processTime":
            PageName = "Variance of Process Time"

        elif PageName == "incorrectRoles":
            PageName = "Incorrect resource/roles"
        elif PageName == "change":
            PageName = "Interface or media change"
        elif PageName == "upload":
            return render_template("Upload.html")
        else:
            PageName = PageName


    else:
        PageName = "Home"

    if not df.empty:
        temp = df.to_dict('records')
        columnNames = df.columns.values
    df.drop(df.index, inplace=True)
    return render_template("index.html", PageName=PageName,
                           records=temp, colnames=columnNames)


@app.route('/upload/csv', methods=['GET', 'POST'])
def upload():
    global logSorted
    f="No File "
    if request.method == 'POST' and 'csv' in request.form.keys():

        f = request.form['csv']
        log_csv = pd.read_csv(f, sep=',')
        log_csv['row_num'] = np.arange(len(log_csv)) + 2
        log_csv.rename(columns={'Case ID': 'case:Case ID'}, inplace=True)

        parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case:Case ID',

                      }
        '''parameters={constants.PARAMETER_CONSTANT_CASEID_KEY: "Case ID",
                                                           constants.PARAMETER_CONSTANT_ACTIVITY_KEY: "Activity",
                                                            constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY:"Start Timestamp",
                                                            constants.PARAMETER_CONSTANT_RESOURCE_KEY:"Resource",
                                                            constants.PARAMETER_CONSTANT_TIMESTAMP_KEY:"Complete Timestamp"
                                                           }'''
        event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
        logSorted = sorting.sort_timestamp(event_log, "Start Timestamp", False)



    return redirect(f"../{f} uploaded")


if __name__ == "__main__":
    app.run(debug=True)


def main():
    log_csv = pd.read_csv('Production_Data.csv', sep=',')
    log_csv['row_num'] = np.arange(len(log_csv)) + 2
    log_csv.rename(columns={'Case ID': 'case:Case ID'}, inplace=True)

    parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case:Case ID',

                  }
    '''parameters={constants.PARAMETER_CONSTANT_CASEID_KEY: "Case ID",
                                                       constants.PARAMETER_CONSTANT_ACTIVITY_KEY: "Activity",
                                                        constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY:"Start Timestamp",
                                                        constants.PARAMETER_CONSTANT_RESOURCE_KEY:"Resource",
                                                        constants.PARAMETER_CONSTANT_TIMESTAMP_KEY:"Complete Timestamp"
                                                       }'''
    event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    logSorted = sorting.sort_timestamp(event_log, "Start Timestamp", False)

    blacklist = ['Lapping - Machine 1', 'Turning & Milling - Machine 8']

    # Unwanted_Activity(logSorted, blacklist)
    Backloop(logSorted)
    # Redundant_Activity(logSorted)
    # Interface(logSorted)
    # maxTime=86400
    # Idle_time(logSorted, maxTime)
    # Variance_of_process_times(logSorted)
    # Bottleneck(logSorted)
    ##Parallelizable_tasks_loglevel()
    # Parallelizable_tasks_CaseLevel()

    # dontFollowList=[('Setup - Machine 8', 'Packing')]
    # Eventually_follows(dontFollowList)

    # Roles_discovery()
