__author__ = 'sottilep'

from pymongo import MongoClient
from IPython.parallel import Client

# Initiate IPNotebook Parallel Computing
ipclient = Client()
print(ipclient.ids)
ipview = ipclient.load_balanced_view()

# Initiate MongoDB Access
client = MongoClient()
db = client.VentDyssynchrony_db
breath_data = db.BreathData_collection
patient_data = db.PatientData_collection
log_data = db.LogData_collection
vent_data = db.VentSettings_collection
RN_data = db.RNData_collection
RT_data = db.RTData_collection
Lab_data = db.LabData_collection


@ipview.parallel(block = True)
def data_entry(data_files):
    import pandas as pd
    import scipy.stats as stats
    import numpy as np
    import matplotlib.pyplot as plt
    import datetime as dt
    from pymongo import MongoClient
    import pymongo
    import sys

    # Open Mongos for Each Engine for Parallel Inputs
    client = MongoClient()
    db = client.VentDyssynchrony_db
    breath_data = db.BreathData_collection
    patient_data = db.PatientData_collection
    log_data = db.LogData_collection
    vent_data = db.VentSettings_collection
    RN_data = db.RNData_collection
    RT_data = db.RTData_collection
    Lab_data = db.LabData_collection

    # Define Location Function
    def get_location(group, errors):
        try:
            location = int(pd.to_datetime(group.DateTime.min(), coerce = True).value)
        except:
            location = 0
            errors.appends('location conversion failed')
        return (location, errors)

    # Define Elapse Time Calculator:
    def get_ElapseTime(df, errors):
        try:
            elapsetime = pd.to_timedelta(df.DateTime.max() - df.DateTime.min(), unit = 's')
        except:
            elapsetime = 0
            errors.append('DateTime NAT')
            print(patients, files, df.DateTime.max(), df.DateTime.min())
        return (elapsetime, errors)

    # Define Pressure and Flow Extrema Calculator (returns tuple(value, time, location))
    def pres_flow_extrema(group):
        pass

    # Define File Cleanup Function
    def file_cleaner(file_path, file_type):
        errors = []

        if file_type == 'wave' or file_type == 'breath':
            try:
                df = pd.read_csv(file_path, sep = '\t', header = 1, error_bad_lines = False,
                                 parse_dates = {'DateTime': ['Date', 'HH:MM:SS']},
                                 infer_datetime_format = True, dayfirst = True, na_values = '--')
            except:
                errors.append('Error on CSV load')
                print(patients, files)

            try:
                df['DateTime'] = pd.to_datetime(df['DateTime'], dayfirst = True, infer_datetime_format = True,
                                                coerce = True)
            except:
                errors.append('Error in DateTime Load')
                print(patients, files, df.DateTime, sys.exc_info()[0])

            if file_type == 'wave':
                df['ElapseTime'] = pd.to_timedelta(df['Time(ms)'], unit = 'ms')
                df.reset_index(inplace = True, drop = False)

                if stats.linregress(df.index, df['Time(ms)'])[2] < 0.95:
                    errors.append(
                        'time frame not continous, ' + 'r = ' + str(stats.linregress(df.index, df['Time(ms)'])[2]))
                    df.plot(x = 'index', y = 'Time(ms)')
                    plt.title(file_path)

                breath_diff = np.diff(df.Breath)
                if breath_diff.any() != 1 or 0:
                    errors.append('breath count not continous')
                    df.plot(x = 'index', y = 'Breath')
                    plt.title(file_path)

                df.drop(['Paux (cmH2O)', 'CO2 (mmHg)', 'Comment', 'Time(ms)'], axis = 1, inplace = True)

            elif file_type == 'breath':
                df.drop(['Flow Pattern', 'MMV (l/min)', 'ExpMinVol Lo (l/min)', 'ExpMinVol Hi (l/min)', '%MinVol (%)',
                         'Pressure Hi (cmH2O)',
                         'Pcontrol (cmH2O)', 'Paux/Paw', 'Int. Controller', 'f cmv (b/min)', 'f simv (b/min)',
                         'Rate Hi (b/min)',
                         'Oxygen Lo (%)', 'Oxygen Hi (%)', 'P0.1 (cmH2O)', 'Pinsp (cmH2O)', 'PetCO2 (mmHg)', 'SpO2 (%)',
                         'Pulse (l/min)', 'HLI (%)', 'Variab. Index (%)', 'Oxygen (%).1', 'Rcexp (s)', 'Rcinsp (s)',
                         'WOB (J/l)',
                         'PTP (cmH2O*s)', '!High Pressure', '!Disconn. Patient', '!Apnea', '!Low MinVol',
                         '!High MinVol',
                         '!High Rate', '!General Alarm', '!Silence', '!Fail to Cycle', '!Disconn. Vent.',
                         '!Loss of PEEP',
                         '!Oxygen conc.', '!Operator', '!Gas Supply', '!SpezAlarm', 'ETS (%)', 'Body Wt (kg)', 'I:E.1'],
                        axis = 1, inplace = True)
                df.rename(columns = {'Vt (ml)': 'Set Vt', 'Peep (cmH2O)': 'PEEP', 'Mode': 'Vent Mode',
                                     'f cmv (b/min)': 'Set RR', 'Oxygen (%)': 'FiO2'}, inplace = True)
                df.reset_index(inplace = True, drop = False)

        else:
            try:
                if file_type == 'lab':
                    df = pd.read_csv(path + '\\' + patients + '\\' + files, na_values = '--',
                                     infer_datetime_format = True,
                                     parse_dates = {'DateTime': ['Date/Times']}, error_bad_lines = False)
                else:
                    df = pd.read_csv(path + '\\' + patients + '\\' + files, na_values = '--',
                                     infer_datetime_format = True,
                                     parse_dates = ['DateTime'], error_bad_lines = False)
            except:
                errors.append('Error on CSV load')
                print(patients, files, sys.exc_info()[:1])

            try:
                df['DateTime'] = pd.to_datetime(df['DateTime'], infer_datetime_format = True, coerce = True)
            except:
                errors.append('Error in DateTime Load')
                print(patients, files, df.DateTime, sys.exc_info()[:1])

            df.dropna(axis = 0, how = 'all', inplace = True)
            df.reset_index(inplace = True, drop = False)

            if file_type == 'rn':
                try:
                    df.drop(['Unnamed: 35', 'A-line MAP.1'], axis = 1, inplace = True)
                except:
                    pass
                try:
                    df.rename(columns = {'Set Vt (mLs)': 'Set Vt', 'HOB Position': 'HOB', 'PEEP (cmH20)': 'PEEP',
                                         'FIO2': 'FiO2'}, inplace = True)
                except:
                    pass
                try:
                    df['PEEP'] = df['PEEP'].str.rstrip(' cmH2O')
                except:
                    pass
                df.replace(to_replace = {
                    'Vent Mode': {'APV;CMV': 'APVCMV', 'PRVC': 'APVCMV', 'PSV;CPAP': 'SPONT', 'CPAP': 'SPONT',
                                  'CMV': 'APVCMV', 'PCMV': 'PCV', 'APV': 'APVCMV', 'CMV;APV': 'APVCMV'}},
                    inplace = True)

            elif file_type == 'rt':
                try:
                    df.drop(['Auto Flow', 'Exhaled Vt', 'Cuff Pressure', 'Actual Ve', 'Set Ve', 'Unnamed: 25',
                             'Spontaneous Vt'], axis = 1, inplace = True)
                except:
                    pass
                try:
                    df['PEEP'] = df['PEEP'].str.rstrip(' cmH2O')
                except:
                    pass
                df.replace(to_replace = {
                    'Vent Mode': {'APV;CMV': 'APVCMV', 'PRVC': 'APVCMV', 'PSV;CPAP': 'SPONT', 'CPAP': 'SPONT',
                                  'CMV': 'APVCMV', 'PCMV': 'PCV', 'APV': 'APVCMV', 'CMV;APV': 'APVCMV'}},
                    inplace = True)

            elif file_type == 'lab':
                for head in df.columns:
                    new_head = head.lstrip()
                    new_head = head.lower()

                    if '.' in head:
                        df.rename(columns = {head: new_head.split('.')[0] + new_head.split('.')[1]}, inplace = True)
                    else:
                        df.rename(columns = {head: new_head}, inplace = True)

                    if head == 'DateTime' or new_head == 'datetime':
                        df.rename(columns = {'datetime': 'DateTime'}, inplace = True)

        try:
            if df.DateTime.any() == np.nan:
                errors.append('DateTime with NAN')
        except:
            print(patients, files, sys.exc_info()[:1])

        return (df, errors)

    # Main Loop through each file
    for data in data_files:
        path = data[0]
        patients = data[1]
        files = data[2]

        if 'Waveform' in files:
            df, errors = file_cleaner(path + '\\' + patients + '\\' + files, 'wave')
            groups = df.groupby('Breath')
            for name, group in groups:

                try:
                    location = int(group.DateTime.astype(np.int64).min())
                except:
                    location = 0
                    errors.append('location conversion failed')

                max_pressure, max_flow, min_pressure, min_flow = pres_flow_extrema(group)

                try:
                    insp_time = group[group.Status != 0]['ElapseTime'].dt.to_pytimedelta().max().total_seconds() - \
                                group[group.Status != 0]['ElapseTime'].dt.to_pytimedelta().min().total_seconds()
                except:
                    insp_time = 0
                    errors.append('could not calculate iTime: ' + str(name))

                try:
                    breath_time = group.ElapseTime.dt.to_pytimedelta().max().total_seconds() - \
                                  group.ElapseTime.dt.to_pytimedelta().min().total_seconds()
                except:
                    breath_time = 0
                    errors.append('could not calculate breath_time: ' + str(name))

                data_document = {
                    '_id': patients + '\\WF' + str(group.Breath.min()) + '\\' + str(group.DateTime.min()),
                    'patientID': patients,
                    'file_name': patients + '\\' + files,
                    'breath_number': int(group.Breath.max()),
                    'start_time': group.DateTime.dt.to_pydatetime().min(),  # str(group.DateTime.min())
                    'end_time': group.DateTime.dt.to_pydatetime().max(),
                    'location': [location, 0],
                    'characteristics': {'breath_time': breath_time,
                                        'insp_time': insp_time,
                                        'exp_time': breath_time - insp_time,
                                        'peak_pressure': group['Paw (cmH2O)'].max(),
                                        'min_pressure': group['Paw (cmH2O)'].min(),
                                        'peak_insp_flow': group[group.Status == 0]['Flow (l/min)'].max(),
                                        'min_exp_flow': group[group.Status == 1]['Flow (l/min)'].max(),
                                        'max_vol': group['Volume (ml)'].max(),
                                        'min_vol': group['Volume (ml)'].min(),
                                        'end_insp_vol': group[group.Status == 0]['Volume (ml)'].tail(10).min(),
                                        'max_pressure': str(max_pressure),
                                        'max_flow': str(max_flow),
                                        'min_pressure': str(min_pressure),
                                        'min_flow': str(min_flow)},
                    'data_frame': {'DateTime': group.DateTime.dt.to_pydatetime().tolist(),
                                   'Time': group.ElapseTime.values.tolist(),
                                   'Status': group.Status.values.tolist(),
                                   'Paw': group['Paw (cmH2O)'].values.tolist(),
                                   'Flow': group['Flow (l/min)'].values.tolist(),
                                   'Volume': group['Volume (ml)'].values.tolist()}}

                try:
                    breath_data.insert(data_document)
                except:
                    print(patients, files, sys.exc_info()[:1])
            elapsetime = df.ElapseTime.max()

        elif 'Breath' in files:
            df, errors = file_cleaner(path + '\\' + patients + '\\' + files, 'breath')
            groups = df.groupby('index')
            for name, group in groups:
                location, errors = get_location(group, errors)
                group.dropna(axis = 1, how = 'any', inplace = True)
                if group.size > 0:
                    try:
                        data_document = {
                            '_id': patients + '\\Vent' + str(group.index.min()) + '\\' + str(group.DateTime.min()),
                            'patientID': patients,
                            'file_name': patients + '\\' + files,
                            'breath_number': int(group.index.max()),
                            'breath_time': group.DateTime.dt.to_pydatetime().min(),
                            'vent_settings': group.to_dict(orient = 'records'),
                            'location': [location, 0]}

                        try:
                            vent_data.insert(data_document)
                        except pymongo.errors.DuplicateKeyError:
                            pass
                    except:
                        errors.append('No DateTime on Insert ' + patients + '\\' + files + str(name))
            elapsetime, errors = get_ElapseTime(df, errors)

        elif 'RN' in files:
            df, errors = file_cleaner(path + '\\' + patients + '\\' + files, 'rn')
            groups = df.groupby('index')
            for name, group in groups:
                location, errors = get_location(group, errors)
                group.dropna(axis = 1, how = 'any', inplace = True)
                if group.size > 0:
                    try:
                        data_document = {
                            '_id': patients + '\\RN' + str(group.index.min()) + '\\' + str(group.DateTime.min()),
                            'patientID': patients,
                            'file_name': patients + '\\' + files,
                            'entry_number': int(group.index.max()),
                            'entry_time': group.DateTime.dt.to_pydatetime().min(),
                            'RN_entry': group.to_dict(orient = 'records'),
                            'location': [location, 0]}

                        try:
                            RN_data.insert(data_document)
                        except pymongo.errors.DuplicateKeyError:
                            pass

                    except:
                        errors.append('Not DateTime' + patients + files)

            elapsetime, errors = get_ElapseTime(df, errors)

        elif 'RT' in files:
            df, errors = file_cleaner(path + '\\' + patients + '\\' + files, 'rt')
            groups = df.groupby('index')
            for name, group in groups:
                location, errors = get_location(group, errors)
                group.dropna(axis = 1, how = 'any', inplace = True)
                if group.size > 0:
                    data_document = {
                        '_id': patients + '\\RT' + str(group.index.min()) + '\\' + str(group.DateTime.min()),
                        'patientID': patients,
                        'file_name': patients + '\\' + files,
                        'entry_number': int(group.index.max()),
                        'entry_time': group.DateTime.dt.to_pydatetime().min(),
                        'RT_entry': group.to_dict(orient = 'records'),
                        'location': [location, 0]}
                    try:
                        RT_data.insert(data_document)
                    except pymongo.errors.DuplicateKeyError:
                        pass
            elapsetime, errors = get_ElapseTime(df, errors)

        elif 'Lab' in files:
            df, errors = file_cleaner(path + '\\' + patients + '\\' + files, 'lab')
            groups = df.groupby('index')
            for name, group in groups:
                location, errors = get_location(group, errors)
                group.dropna(axis = 1, how = 'any', inplace = True)
                if group.size > 0:
                    data_document = {
                        '_id': patients + '\\Lab' + str(group.index.min()) + '\\' + str(group.DateTime.min()),
                        'patientID': patients,
                        'file_name': patients + '\\' + files,
                        'entry_number': int(group.index.max()),
                        'entry_time': group.DateTime.dt.to_pydatetime().min(),
                        'Lab_entry': group.to_dict(orient = 'records'),
                        'location': [location, 0]}
                    try:
                        Lab_data.insert(data_document)
                    except pymongo.errors.DuplicateKeyError:
                        pass
            elapsetime, errors = get_ElapseTime(df, errors)

        log_document = {
            '_id': patients + '\\' + files,
            'patientID': patients,
            'file_name': files,
            'update_date': dt.datetime.now(),
            'n_data': len(df.index),
            'start_time': df.DateTime.dt.to_pydatetime().min(),
            'end_time': df.DateTime.dt.to_pydatetime().max(),
            'elapse_time': elapsetime.total_seconds(),
            'file_errors': errors,
            'location': [pd.to_datetime(df.DateTime.min(), coerce = True).value, 0]}
        log_data.insert(log_document)

    return
