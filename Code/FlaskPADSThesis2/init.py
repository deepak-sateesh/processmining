from IPython.core.display import HTML
from flask import Flask, render_template, request, redirect
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.util import sorting
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.organizational_mining.roles import algorithm as roles_discovery
import numpy as np
from pm4py.statistics.eventually_follows.log import get as efg_get
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization
from flask import Markup
import xml.etree.ElementTree as ET

from pm4py.algo.filtering.log import ltl as ll

app = Flask(__name__)
log_csv=[]
cols = ['Detected Weakness Row', 'Case ID', 'Weakness Type (AF/PA)', 'Weakness ID', 'Weakness Origin', 'Weakness Time',
        'Weakness Information', 'Weakness Measurement', 'Weakness Level']
dontFollowList = [('Setup - Machine 8', 'Packing')]
blacklist = ['Lapping - Machine 1', 'Turning & Milling - Machine 8']
activitySet=set()
maxTime = 86400
df = pd.DataFrame(columns=cols)
f = "No File "
i=0
logSorted = []
Nodes=[]
Edges=[]

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
    global Nodes, Edges
    Nodes.clear()
    Edges.clear()
    Nodes=[]
    Edges=[]
    caseList = []
    edgeList = []
    for case_index, case in enumerate(log):
        eventList = []
        lrs = ""
        indexList = []
        for event_index, event in enumerate(case):
            eventList.append(event["Activity"])
        if Find_sequence(eventList) is not None:
            lrs = Find_sequence(eventList)
            caseList.append(case.attributes['Case ID'])
            # print("Repeating sequence for events in case:",case.attributes['concept:name']," is: ", lrs)
            #print("LRS:=>",lrs)

            Nodes=Nodes+lrs
            n=len(lrs)
            for i in range(n-1):
                edgeList.append((lrs[i], lrs[i+1]))

            row = {cols[0]: event['row_num'], cols[1]: case.attributes['Case ID'], cols[2]: 'AF', cols[3]: '2',
                   cols[4]: 'Automatic detection', cols[5]: '', cols[6]: 'Backloop {' + ''.join(lrs) + '}',
                   cols[7]: 'In the case', cols[8]: 'Process level'}
            df = df.append(row, ignore_index=True)





    caseSet=set(caseList)

    n=len(caseList)
    #print("Nodes bef->", Nodes)
    #print("Nodes bef->", Nodes)
    '''for i in range(n):
        if(i<n):
            edgeList.append((caseList[0],caseList[1]))'''
    if Edges is not None:
        Edges=set(edgeList)
    if Nodes is not None:
        Nodes = set(Nodes)

    print("Nodes->", Nodes)
    DisplayCaseFilteredDFG(caseSet,"Backloop")
    #for trace in event_log:
    #    print(trace)

def DisplayCaseFilteredDFG(CaseList, src):
    global log_csv
    filteredCasesLogCSV=[]

    global  Nodes, Edges

    #print(log_csv.shape)
    #print(filteredCasesLogCSV.shape)
    log_csv.rename(columns={'Activity': 'concept:name', 'Start Timestamp': 'time:timestamp'}, inplace=True)
    log_csv["time:timestamp"] = log_csv["time:timestamp"].apply(pd.to_datetime)
    filteredCasesLogCSV = log_csv[log_csv['case:Case ID'].isin(CaseList)]



    parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case:Case ID'}
    event_log5 = log_converter.apply(filteredCasesLogCSV, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    event_log5 = sorting.sort_timestamp(event_log5, "time:timestamp", False)

    dfg_simple4 = dfg_discovery.apply(event_log5, variant=dfg_discovery.Variants.FREQUENCY)
    parameters = {dfg_visualization.Variants.FREQUENCY.value.Parameters.FORMAT: "svg"}
    gviz = dfg_visualization.apply(dfg_simple4, log=event_log5, variant=dfg_visualization.Variants.FREQUENCY,
                                   parameters=parameters)
    #print(dfg_visualization.view(gviz))
    #print(gviz)

    if(src=="Backloop"):
        dfg_visualization.save(gviz, "./SVGs/Backloop.svg")
        mytree = ET.parse('./SVGs/Backloop.svg')
        myroot = mytree.getroot()
        NodesDict={}
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'node'):
                    n = gg.find('{http://www.w3.org/2000/svg}text').text
                    nWithoutCount=n.split(" (")
                    if (nWithoutCount[0] in Nodes):
                        # chAttrb = gg.find('{http://www.w3.org/2000/svg}polygon').attrib
                        # print((chAttrb.keys())[0])
                        temp=gg.find('{http://www.w3.org/2000/svg}title').text
                        print(temp)
                        print("nWithoutCount=>",nWithoutCount)
                        NodesDict[nWithoutCount[0]] = gg.find('{http://www.w3.org/2000/svg}title').text
                        gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')

        print("NodesDict=>",NodesDict)
        print("Edges=>",Edges)
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'edge'):
                    for (s, d) in Edges:
                        title = gg.find('{http://www.w3.org/2000/svg}title').text
                        t = [title.split('->')]
                        if(s in NodesDict.keys() and d in NodesDict.keys()):
                            if (NodesDict[s] == t[0][0] and NodesDict[d] == t[0][1]):
                                print((s, NodesDict[s], t[0][0], d, NodesDict[d], t[0][1],
                                       gg.find('{http://www.w3.org/2000/svg}title').text))
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('stroke', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}path').set('stroke', '#800000')
        mytree.write('./ModifiedSVGs/backloopModified.svg')

    elif (src == "Eventually_follows"):
        dfg_visualization.save(gviz, "./SVGs/Eventually_follows.svg")
        mytree = ET.parse('./SVGs/Eventually_follows.svg')
        myroot = mytree.getroot()
        NodesDict = {}
        print("Eventually follows DisplayCaseFilteredDFG")
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'node'):
                    n = gg.find('{http://www.w3.org/2000/svg}text').text
                    nWithoutCount = n.split(" (")
                    if (nWithoutCount[0] in Nodes):
                        # chAttrb = gg.find('{http://www.w3.org/2000/svg}polygon').attrib
                        # print((chAttrb.keys())[0])
                        temp = gg.find('{http://www.w3.org/2000/svg}title').text
                        print(temp)
                        print("nWithoutCount=>", nWithoutCount)
                        NodesDict[nWithoutCount[0]] = gg.find('{http://www.w3.org/2000/svg}title').text
                        gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')

        print("NodesDict=>", NodesDict)
        print("Edges=>", Edges)
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'edge'):
                    for (s, d) in Edges:
                        title = gg.find('{http://www.w3.org/2000/svg}title').text
                        t = [title.split('->')]
                        if (s in NodesDict.keys() and d in NodesDict.keys()):
                            if (NodesDict[s] == t[0][0] and NodesDict[d] == t[0][1]):
                                print((s, NodesDict[s], t[0][0], d, NodesDict[d], t[0][1],
                                       gg.find('{http://www.w3.org/2000/svg}title').text))
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('stroke', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}path').set('stroke', '#800000')

        mytree.write('./ModifiedSVGs/Eventually_followsModified.svg')

    elif (src == "Parallelizable_tasks_ProcessCaseLevel"):
        dfg_visualization.save(gviz, "./SVGs/Parallelizable_tasks_ProcessCaseLevel.svg")
        mytree = ET.parse('./SVGs/Parallelizable_tasks_ProcessCaseLevel.svg')
        myroot = mytree.getroot()
        NodesDict = {}
        print("Parallelizable_tasks_ProcessCaseLevel DisplayCaseFilteredDFG")
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'node'):
                    n = gg.find('{http://www.w3.org/2000/svg}text').text
                    nWithoutCount = n.split(" (")
                    if (nWithoutCount[0] in Nodes):
                        # chAttrb = gg.find('{http://www.w3.org/2000/svg}polygon').attrib
                        # print((chAttrb.keys())[0])
                        temp = gg.find('{http://www.w3.org/2000/svg}title').text
                        print(temp)
                        print("nWithoutCount=>", nWithoutCount)
                        NodesDict[nWithoutCount[0]] = gg.find('{http://www.w3.org/2000/svg}title').text
                        gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')

        print("NodesDict=>", NodesDict)
        print("Edges=>", Edges)
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'edge'):
                    for (s, d) in Edges:
                        title = gg.find('{http://www.w3.org/2000/svg}title').text
                        t = [title.split('->')]
                        if (s in NodesDict.keys() and d in NodesDict.keys()):
                            if (NodesDict[s] == t[0][0] and NodesDict[d] == t[0][1]):
                                print((s, NodesDict[s], t[0][0], d, NodesDict[d], t[0][1],
                                       gg.find('{http://www.w3.org/2000/svg}title').text))
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('stroke', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}path').set('stroke', '#800000')

        mytree.write('./ModifiedSVGs/Parallelizable_tasks_ProcessCaseLevelModified.svg')

    elif (src == "Redundant_Activity"):
        dfg_visualization.save(gviz, "./SVGs/Redundant_Activity.svg")
        mytree = ET.parse('./SVGs/Redundant_Activity.svg')
        myroot = mytree.getroot()
        NodesDict = {}
        print("Redundant_Activity DisplayCaseFilteredDFG")
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'node'):
                    n = gg.find('{http://www.w3.org/2000/svg}text').text
                    nWithoutCount = n.split(" (")
                    if (nWithoutCount[0] in Nodes):
                        # chAttrb = gg.find('{http://www.w3.org/2000/svg}polygon').attrib
                        # print((chAttrb.keys())[0])
                        temp = gg.find('{http://www.w3.org/2000/svg}title').text
                        print(temp)
                        print("nWithoutCount=>", nWithoutCount)
                        NodesDict[nWithoutCount[0]] = gg.find('{http://www.w3.org/2000/svg}title').text
                        gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')

        print("NodesDict=>", NodesDict)
        print("Edges=>", Edges)
        for g in myroot.findall('{http://www.w3.org/2000/svg}g'):
            for gg in g.findall('{http://www.w3.org/2000/svg}g'):
                if (gg.get('class') == 'edge'):
                    for (s, d) in Edges:
                        title = gg.find('{http://www.w3.org/2000/svg}title').text
                        t = [title.split('->')]
                        if (s in NodesDict.keys() and d in NodesDict.keys()):
                            if (NodesDict[s] == t[0][0] and NodesDict[d] == t[0][1]):
                                print((s, NodesDict[s], t[0][0], d, NodesDict[d], t[0][1],
                                       gg.find('{http://www.w3.org/2000/svg}title').text))
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('fill', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}polygon').set('stroke', '#800000')
                                gg.find('{http://www.w3.org/2000/svg}path').set('stroke', '#800000')

        mytree.write('./ModifiedSVGs/Redundant_ActivityModified.svg')

    elif(src=="Parallelizable_tasks_ProcessCaseLevel"):
        print("Parallelizable_tasks_ProcessCaseLevel DisplayCaseFilteredDFG")




def Eventually_follows(lt):
    global df
    global f
    global log_csv
    global Nodes, Edges
    Nodes = []
    Edges=[]
    caseList=[]
    log_csv = pd.read_csv(f, sep=',')
    log_csv['row_num'] = np.arange(len(log_csv)) + 2
    # print(log_csv)
    log_csv.rename(columns={'Case ID': 'case:Case ID'}, inplace=True)
    log_csv.rename(columns={'Start Timestamp': 'time:timestamp'}, inplace=True)
    log_csv.rename(columns={'Activity': 'concept:name'}, inplace=True)

    parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case:Case ID',

                  }
    '''parameters={constants.PARAMETER_CONSTANT_CASEID_KEY: "Case ID",
                                                       constants.PARAMETER_CONSTANT_ACTIVITY_KEY: "Activity",
                                                        constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY:"Start Timestamp",
                                                        constants.PARAMETER_CONSTANT_RESOURCE_KEY:"Resource",
                                                        constants.PARAMETER_CONSTANT_TIMESTAMP_KEY:"Complete Timestamp"
                                                       }'''
    event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    ls = sorting.sort_timestamp(event_log, "time:timestamp", False)

    efg_graph = efg_get.apply(ls)


    for e in efg_graph.keys():
        if e in lt:
            print("Followed times:", (e, efg_graph[e]))
            Nodes.append(e[0])
            Nodes.append(e[1])

            Edges.append(e)

    for case_index, case in enumerate(ls):
        # print(case.attributes['Case ID'] )

        eList = []
        for event_index, event in enumerate(case):
            # print (event_index,event)
            eList.append((event["concept:name"], event["row_num"], case.attributes['Case ID'], event["time:timestamp"]))

        # print("Elist", eList)

        for l1, l2 in lt:
            prev_e = []
            follow_e = []
            found_l1 = False
            for e in eList:
                if (l1 == e[0]):
                    prev_e = e
                    found_l1 = True
                if (found_l1 and l2 == e[0]):
                    follow_e = e
                    break
            if (len(follow_e) > 0):
                print(prev_e, follow_e)
                row = {cols[0]: str(prev_e[1]) + ", " + str(follow_e[1]), cols[1]: prev_e[2], cols[2]: 'AF',
                       cols[3]: '10', cols[4]: 'Expert', cols[5]: prev_e[3] + ", " + follow_e[3],
                       cols[6]: 'Unwanted follow \"' + prev_e[0] + '\", \"' + follow_e[0] + '\"',
                       cols[7]: 'In the case', cols[8]: 'Case level'}
                df = df.append(row, ignore_index=True)
                caseList.append(prev_e[2])
    caseList=set(caseList)
    if Nodes is not None:
        Nodes = set(Nodes)
    DisplayCaseFilteredDFG(caseList,"Eventually_follows")

def Parallelizable_tasks_ProcessCaseLevel():
    global df
    global f
    caseList=[]
    print("Parallelizable_tasks_CaseLevel function\n\n")
    log_csv3 = pd.read_csv(f, sep=',')
    log_csv3.rename(columns={'Activity': 'concept:name','Start Timestamp':'time:timestamp'}, inplace=True)
    log_csv3["time:timestamp"] = log_csv3["time:timestamp"].apply(pd.to_datetime)

    parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'Case ID'}
    event_log3 = log_converter.apply(log_csv3, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    event_log3 = sorting.sort_timestamp(event_log3, "time:timestamp", False)

    print("Eventlog3", event_log3)
    for case_index, case in enumerate(event_log3):
        # print(case)
        tracefilter_log_pos = attributes_filter.apply(event_log3, [case.attributes["concept:name"]],
                                                      parameters={attributes_filter.Parameters.ATTRIBUTE_KEY: "Case ID",
                                                                  attributes_filter.Parameters.POSITIVE: True})

        dfg_simple3 = dfg_discovery.apply(tracefilter_log_pos)

        l = []
        for k in dfg_simple3.keys():
            if (k[0] != k[1]):
                if (k[1], k[0]) in dfg_simple3.keys():
                    l.append((k[1], k[0]))
        l1 = []
        for i in l:
            if (i[1], i[0]) in l:
                l1.append((i[0], i[1]))
                l.remove((i[1], i[0]))
                l.remove((i[0], i[1]))
        if (len(l) > 0):
            row = {cols[0]: case.attributes['concept:name'], cols[1]: case.attributes['concept:name'], cols[2]: 'AF',
                   cols[3]: '9', cols[4]: 'Automatic detection', cols[5]: '',
                   cols[6]: 'Parallelizable tasks :' + ''.join(str(l1)), cols[7]: 'In the Process',
                   cols[8]: 'Process level'}
            caseList.append(case.attributes['concept:name'])
            df = df.append(row, ignore_index=True)
            # print("\n\nParallelizable tasks for Case:",case.attributes["concept:name"]," are => ", end=" ")
            # print(l1)
    caseList=set(caseList)
    DisplayCaseFilteredDFG(caseList,"Parallelizable_tasks_ProcessCaseLevel")

def find_duplicate_events(x):
    _size = len(x)
    duplicate_list = []
    for i in range(_size):
        k = i + 1
        for j in range(k, _size):
            if x[i] == x[j] and x[i] not in duplicate_list:
                duplicate_list.append(x[i])
    return duplicate_list


def Redundant_Activity(log):
    global df, Nodes, Edges
    Nodes=[]
    Edges=[]
    caseList=[]
    print("Redundant_Activity function")
    for case_index, case in enumerate(log):
        # print("\n Case Id: %s" % ( case.attributes["concept:name"]))
        event_list = []

        for event_index, event in enumerate(case):
            # print("event start time: %s  event activity: %s" % (event["Start Timestamp"], event["Activity"]))
            event_list.append(event["Activity"])
        duplicateEventList = []
        duplicateEventList = find_duplicate_events(event_list)
        # print ("The events which got repeated in the trace are",duplicateEventList)
        if (len(duplicateEventList) > 0):
            row = {cols[0]: event['row_num'], cols[1]: case.attributes['Case ID'], cols[2]: 'AF', cols[3]: '3',
                   cols[4]: 'Automatic detection', cols[5]: "",
                   cols[6]: 'Redundant Activities list: \"' + ''.join(duplicateEventList) + '\"',
                   cols[7]: 'In the Process', cols[8]: 'Process Level'}
            caseList.append(case.attributes['concept:name'])
            Nodes.append(event["Activity"])
            df = df.append(row, ignore_index=True)
    caseList = set(caseList)
    Nodes=set(Nodes)
    #print("Nodes=>", Nodes)
    DisplayCaseFilteredDFG(caseList, "Redundant_Activity")

def Unwanted_Activity(log, blacklist):
    global df, cols
    print("Unwanted activity function")
    for case_index, case in enumerate(log):
        # print(case.attributes['Case ID'] )
        for event_index, event in enumerate(case):
            # print (event_index,event)
            if (event["Activity"] in blacklist):
                # case.attributes['Case ID']+"-> Event "+str(event_index+1)print("Unwanted activity=> activity: %s -> case: %s that started @ %s " % (event["Activity"], event["Case ID"], event["Start Timestamp"]))
                row = {cols[0]: event['row_num'], cols[1]: case.attributes['Case ID'], cols[2]: 'AF', cols[3]: '1',
                       cols[4]: 'Expert', cols[5]: event["Start Timestamp"],
                       cols[6]: 'Unwanted activity \"' + event["Activity"] + '\"', cols[7]: 'In the case',
                       cols[8]: 'Activity level'}
                df = df.append(row, ignore_index=True)


def Bottleneck(log):
    global df
    print("Bottleneck function")
    '''for case_index, case in enumerate(log):
        print("\n Case Id: %s" % ( case.attributes["concept:name"]))
        duration=0 
        a=""
        max_duration=0
        for event_index, event in enumerate(case):
            duration=pd.to_datetime(event["Complete Timestamp"], format = "%m/%d/%Y %H:%M:%S")-pd.to_datetime(event["Start Timestamp"], format = "%m/%d/%Y %H:%M:%S")
            if(max_duration==0 or duration>max_duration):
                max_duration=duration
                a=event["Activity"]

        print("Bottleneck Activity at case level:%s took maximum time of %s to complete"%(a,max_duration ))'''
    duration = 0
    a = ""
    max_duration = 0
    for case_index, case in enumerate(log):
        for event_index, event in enumerate(case):
            duration = pd.to_datetime(event["Complete Timestamp"], format="%m/%d/%Y %H:%M:%S") - pd.to_datetime(
                event["Start Timestamp"], format="%m/%d/%Y %H:%M:%S")
            if (max_duration == 0 or duration > max_duration):
                max_duration = duration
                a = event["Activity"]

    print("Bottleneck Activity on log level:%s took maximum time of %s to complete" % (a, max_duration))
    row = {cols[0]: "All Activities", cols[1]: a, cols[2]: 'PA', cols[3]: '8', cols[4]: 'Automatic detection',
           cols[5]: '', cols[6]: 'Activity took maximum time of ' + str(max_duration), cols[7]: 'In the Activity',
           cols[8]: 'Activity Level'}
    df = df.append(row, ignore_index=True)


def Idle_time(log, maxTime):
    global df
    print("Idle_time function")
    for case_index, case in enumerate(log):
        # print("\n Case Id: %s" % ( case.attributes["concept:name"]))
        prev_end_timestamp = 0
        idle_time = 0
        prev_activity = ""
        for event_index, event in enumerate(case):
            if (prev_end_timestamp != 0):
                idle_time = pd.to_datetime(event["Start Timestamp"], format="%m/%d/%Y %H:%M:%S") - prev_end_timestamp
            # print("Idle time between previous activity:%s and current activity:%s is %s"%(prev_activity, event["Activity"], idle_time))
            # if(type(idle_time)!= int):
            #    print(idle_time.total_seconds  )#idle_time/np.timedelta64(1,'s'))
            if (type(idle_time) != int and idle_time.total_seconds() > maxTime):
                # .total_seconds()>7200) :
                row = {cols[0]: event['row_num'], cols[1]: case.attributes['Case ID'], cols[2]: 'PA', cols[3]: '6',
                       cols[4]: 'Expert', cols[5]: event["Start Timestamp"],
                       cols[6]: 'Idletime between ' + prev_activity + ' to ' + event["Activity"] + ' is ' + str(
                           idle_time), cols[7]: 'In the case', cols[8]: 'Event level'}
                df = df.append(row, ignore_index=True)
            prev_end_timestamp = pd.to_datetime(event["Complete Timestamp"], format="%m/%d/%Y %H:%M:%S")
            prev_activity = event["Activity"]


def Variance_of_process_times(log):
    global df
    print("Variance_of_process_times function")
    d = {}  # mean1(log)
    l = []
    for case_index, case in enumerate(log):
        for event_index, event in enumerate(case):
            if event["Activity"] not in d.keys():
                l = []
            else:
                l = d[event["Activity"]]
            l.append((pd.to_datetime(event["Complete Timestamp"], format="%m/%d/%Y %H:%M:%S") - pd.to_datetime(
                event["Start Timestamp"], format="%m/%d/%Y %H:%M:%S")) / pd.Timedelta(hours=1))
            d[event["Activity"]] = (l)
    variance_dict = {}
    for k, v in d.items():
        variance_dict[k] = (min(v), max(v), np.mean(v), np.var(v))
        row = {cols[0]: "All Activities", cols[1]: k, cols[2]: 'PA', cols[3]: '7', cols[4]: 'Automatic detection',
               cols[5]: '', cols[6]: '(Min, Max, Average, Variance) for current activity:' + str(
                (min(v), max(v), np.mean(v), np.var(v))), cols[7]: 'In the Activity', cols[8]: 'Activity Level'}
        df = df.append(row, ignore_index=True)


def Interface(log):
    print("Interface function")
    global df
    for case_index, case in enumerate(log):
        d = {}
        l = ""
        # print("\n Case Id: %s" % ( case.attributes["concept:name"]))

        '''for event_index, event in enumerate(case):
            if( len(d)!=0 and event["Activity"] in d.keys() and event["Resource"]!= d[event["Activity"]]):
                print("The resource has changed for the activity: %s from %s to %s"%(event["Activity"], d[event["Activity"]], event["Resource"]))
            d[event["Activity"]]=event["Resource"]'''
        prev = ""
        for event_index, event in enumerate(case):
            if (prev != "" and event["Resource"] != prev):
                # print("The resource has changed for the activity: \"%s\" from \"%s\" to \"%s\""%(event["Activity"], prev, event["Resource"]))
                row = {cols[0]: event['row_num'], cols[1]: case.attributes['Case ID'], cols[2]: 'AF', cols[3]: '4',
                       cols[4]: 'Automatic detection', cols[5]: event["Start Timestamp"],
                       cols[6]: 'Change of interface for activity ' + event["Activity"] + ' from ' + prev + ' to ' +
                                event["Resource"], cols[7]: 'In the case', cols[8]: 'Event Level'}
                df = df.append(row, ignore_index=True)
            prev = event["Resource"]

def GenerateDFG():
    global f
    print("GenerateDFG")
    log_csv4 = pd.read_csv(f, sep=',')
    log_csv4.rename(columns={'Activity': 'concept:name', 'Start Timestamp': 'time:timestamp'}, inplace=True)
    log_csv4["time:timestamp"] = log_csv4["time:timestamp"].apply(pd.to_datetime)

    parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'Case ID'}
    event_log4 = log_converter.apply(log_csv4, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    event_log4 = sorting.sort_timestamp(event_log4, "time:timestamp", False)

    dfg_simple4 = dfg_discovery.apply(event_log4,  variant=dfg_discovery.Variants.FREQUENCY)
    parameters = {dfg_visualization.Variants.FREQUENCY.value.Parameters.FORMAT: "svg"}
    gviz = dfg_visualization.apply(dfg_simple4, log=event_log4, variant=dfg_visualization.Variants.FREQUENCY, parameters=parameters)
    #print(dfg_visualization.view(gviz))
    dfg_visualization.save(gviz, "MainDFG.svg")
@app.route("/")
@app.route('/<PageName>')
def home(PageName=None):
    global logSorted
    global df, f, i
    temp = ""
    columnNames = ""
    svg=""
    if (PageName != None):
        if(f.strip(" ")=="No File" ):
            print ("empty  file=>",f)
        elif(i<1):
            print("File present=>",f)
            GenerateDFG()
            svg = open('MainDFG.svg').read()
            i=i+1
        if PageName == "backloop":
            PageName = "Backloops"
            df.drop(df.index, inplace=True)
            Backloop(logSorted)
        elif(PageName == "eventuallyFollowsInit"):
            return render_template("EventuallyFollowsInit.html", ActivitySet=activitySet)
        elif (PageName == "eventuallyFollows"):
            df.drop(df.index, inplace=True)
            print("dontFollowList=>",dontFollowList)
            Eventually_follows(dontFollowList)
            PageName = "Eventually Follows"
        elif (PageName == "parallelizableTasks"):
            df.drop(df.index, inplace=True)
            Parallelizable_tasks_ProcessCaseLevel()
            PageName = "Parallelizable Tasks"
        elif (PageName == "redundantActivity"):
            df.drop(df.index, inplace=True)
            Redundant_Activity(logSorted)
            PageName = "Redundant Activity"
        elif (PageName == "unwantedActivityInit"):
            return render_template("unwantedActivityInit.html", ActivitySet=activitySet)
        elif (PageName == "unwantedActivity"):
            df.drop(df.index, inplace=True)
            Unwanted_Activity(logSorted, blacklist)
            PageName = "Unwanted Activity"

        elif PageName == "bottleNeck":
            df.drop(df.index, inplace=True)
            Bottleneck(logSorted)
            PageName = "Bottleneck"
        elif PageName == "idleTime":
            df.drop(df.index, inplace=True)
            Idle_time(logSorted, maxTime)
            PageName = "Idle Time"
        elif PageName == "processTime":
            df.drop(df.index, inplace=True)
            Variance_of_process_times(logSorted)
            PageName = "Variance of Process Time"

        elif PageName == "incorrectRoles":
            df.drop(df.index, inplace=True)
            #Roles_discovery()
            PageName = "Incorrect resource/roles"
        elif PageName == "change":
            df.drop(df.index, inplace=True)
            Interface(logSorted)
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
                           records=temp, colnames=columnNames, svgImage=Markup(svg))


@app.route('/upload/csv', methods=['GET', 'POST'])
def upload():
    global logSorted
    global f, i
    global log_csv
    global activitySet
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
        for case_index, case in enumerate(logSorted):
            lrs = ""
            indexList = []
            for event_index, event in enumerate(case):
                activitySet.add(event["Activity"])

        i=0
    activitySet=sorted(activitySet)
    print("activitySet=>", activitySet)
    return redirect(f"../{f} uploaded")

@app.route('/EventuallyFollowsParameters', methods=['GET', 'POST'])
def parameterEFInit():
    global activitySet
    global dontFollowList
    if request.method == 'POST' :
        P1= request.form['p1']
        P2= request.form['p2']
    dontFollowList=[]
    dontFollowList.append((P1,P2))

    return redirect("../eventuallyFollows")

@app.route('/UnwantedActivityParameter', methods=['GET', 'POST'])
def parameterUnwantedActivityInit():
    global activitySet
    global blackList
    if request.method == 'POST' :
        P= request.form['p']

    blackList=[]
    print("blacklist p=>", P)
    #blackList.join(P)

    return redirect("../unwantedActivity")


if __name__ == "__main__":
    app.run(debug=True)



