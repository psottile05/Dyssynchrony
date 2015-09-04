__author__ = 'sottilep'

import pandas as pd
import pymongo

client = pymongo.MongoClient()
db = client.VentDyssyncrhony_db
breath = db.BreathData_collection

result = breath.find().count()
print(result, type(result))

df = pd.io.json.json_normalize(result)
print(df.head(), df.columns)

# bk.output_file(u'test.html')
# data = dict(Flow=df['vent_settings.p_peak'], Time=df['start_time'])
# bk.show(bk.TimeSeries(data, index='Time'))
