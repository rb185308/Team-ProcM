#!/usr/bin/python

import os, time
import subprocess
import psutil
import re
import ConfigParser
import logging, socket
from datetime import datetime

'''
This script monitors processes listed on config_ini on a server and starts them
if they are not running.
It also checks if the log file is getting executed timely.
'''

def parse_config_file():
    logging.info("Parsing the file")
    parser.read('/home/app/procAlive/config_file.ini')
    config_file_data = {}
    for section_name in parser.sections():
        section_data = {}
        for key, value in parser.items(section_name):
            section_data[key] = value
        config_file_data[section_name] = section_data
    logging.debug("Configuration file parsing completed. {0}".format(config_file_data))
    return config_file_data


def getpids():
    logging.debug("Checking running processes on %s", socket.gethostname())
    for proc in psutil.process_iter():
        with proc.oneshot():
            try:
                pinfo = proc.as_dict(attrs=["pid", "name"])
                process_dict[pinfo['pid']] = pinfo['name']
            except(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                logging.exception("NoSuchProcess", proc)
                pass
    logging.debug("Checking running processes : Completed : {0} ".format(process_dict))
    return process_dict


def checkstatus(data):
    logging.debug("Check the status of the service")
    for key, value in data.items():
        if 'cwd' in value.keys():
            p = psutil.Popen(value['status_cmd'].split(), cwd=value['cwd'], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            q = p.communicate()
            if re.findall('running', str(q[0])) or re.findall('started', str(q[0])):
                if re.findall('not', str(q[0])):
                   logging.debug("Process is not running : {0} ".format(value['name']))
                   cs_stopped_processes.append(value)
                else:
                   logging.debug("Process is running : {0} ".format(value['name']))
                   cs_running_processes.append(value)
            else:
                logging.debug("Process is not running : {0} ".format(value['name']))
                cs_stopped_processes.append(value)
        else:
            p = psutil.Popen(value['status_cmd'].split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            q = p.communicate()
            if re.findall('running', str(q[0])) or re.findall('started', str(q[0])):
                if re.findall('not', str(q[0])):
                   logging.debug("Process is not running : {0} ".format(value['name']))
                   cs_stopped_processes.append(value)
                else:
                   logging.debug("Process is running : {0} ".format(value['name']))
                   cs_running_processes.append(value)
            else:
                logging.debug("Process is not running : {0} ".format(value['name']))
                cs_stopped_processes.append(value)
    return cs_running_processes, cs_stopped_processes


def checkpids(data, all_pids):
    logging.debug("Checking the process IDs")
    running_processes = []
    not_running_processes = []
    for proc_name in data.values():
        if proc_name['name'].lower() in all_pids.values():
            running_processes.append(proc_name)
            logging.debug("PID exists : %s", proc_name['name'].lower())
        else:
            not_running_processes.append(proc_name)
            logging.debug("PID doesn't exists : %s", proc_name['name'].lower())
    return running_processes, not_running_processes


def logrotation(data):
    try:
        logging.debug("Checking log file.")
        for key, value in data.items():
            if 'log_file' in value.keys():
                file_timestamp = datetime.strptime(
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(value['log_file']))),
                    '%Y-%m-%d %H:%M:%S')
                time_now = datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), '%Y-%m-%d %H:%M:%S')
                time_diff = time_now - file_timestamp
                # print(time_diff)
                logging.debug("{0} : Log file not updated from : {1} ".format(value['log_file'],time_diff))
                #print("Time difference is : ",time_diff.seconds)
                if time_diff.seconds >= 10800:
                    log_rotation.append(value)

            else:
                logging.debug("There is no log file listed in configuration file")

    except OSError:
        # print("Path does not exist or is inaccessible")
        logging.error("Path does not exist or is inaccessible")

    return log_rotation


def start_process(not_running_proc):
    for i in not_running_proc:
        logging.debug("starting process : {0} ".format(i['name']))
        if 'cwd' in i:
            psutil.Popen(i['start_cmd'].split(), cwd=i['cwd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)
        else:
            psutil.Popen(i['start_cmd'].split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)

if __name__ == '__main__':
    #Deleting the log file
    try:
        os.remove('/home/app/procAlive/proclive.log')
    except OSError:
        logging.debug('Log file does not exist')
    #start_time = datetime.now()
    """  Calling parse function to read configuartion file """
    logging.basicConfig(filename="proclive.log", format='%(asctime)s - %(message)s', level=logging.DEBUG)
    parser = ConfigParser.RawConfigParser()
    config_data = parse_config_file()
    """ Defining variables for function getpids() """
    process_dict = {}
    """ Calling function to get PID of all running processes """
    all_pids = getpids()
    """ Logic 1 : To check service status """
    """ Defining variables for function checkstatus() """
    cs_running_processes = []
    cs_stopped_processes = []
    """ Calling function to check if service/application is running """
    running_process, stopped_process = checkstatus(config_data)
    if len(stopped_process) != 0:
        start_process(stopped_process)

    """ Logic 2 : To check process IDs """
    """ Defining variables for function checkpids() """
    #running_processes = []
    #not_running_processes = []
    """ Calling function to check if process ID is there in ps -eaf """
    running_proc, not_running_proc = checkpids(config_data, all_pids)
    if len(not_running_proc) != 0:
        start_process(not_running_proc)

    """ Logic 3 : To check if log file is getting updated """
    """ Defining variables for function logrotation() """
    log_rotation = []
    """ Calling function logrotation() """
    log_not_rotating = logrotation(config_data)
    if len(log_not_rotating) != 0:
        start_process(log_not_rotating)


    """Checking if service is running afer executing all above steps .
    If not, then send a mail to respective mail IDs """
    final_running_processes = []
    final_stopped_processes = []
    status_stopped_process = []
    status_stopped_process = []
    """ Calling function to check if service/application is running """
    time.sleep(5)
    logging.debug("Starting final check")
    status_running_process, status_stopped_process = checkstatus(config_data)
    final_running_process, final_stopped_process = checkpids(config_data , getpids())
    if len(final_stopped_process) != 0:
       logging.debug("Sending a mail to ABC as PID file doesn't exists : {0}".format(final_stopped_process))
    elif len(status_stopped_process) != 0:
        logging.debug("Sending a mail to ABC as service status is not running : {0}".format(status_stopped_process))

    logging.debug("Final check completed")
    #end_time = datetime.now()
    #print("Time taken : ", end_time - start_time)
