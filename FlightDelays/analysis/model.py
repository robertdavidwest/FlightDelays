__author__ = 'rwest'
from copy import deepcopy
import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import pandas as pd
from pandas.util import testing
from FlightDelays.config import hdf_path
from FlightDelays.helpers import get_hour, show_stats


def prep_data(xcols, categoricals, data, condition=None, suppress_print=False):
    """Define dependend variables, remove cancellations, encode categoricals and
    make any need variable transforms

    Parameters
    ----------
    xols : list
        list of x variables
    categoricals : list
        list of str categorical variables contained in xols
    data : pd.DataFrame
        the dataset
    condition : str
        any additional condtion to be given to data.query()

    Returns
    -------
    allcols_data : pd.DataFrame
        all data after filtering
    data_x : pd.DataFrame
        the subset of data containing `xcols`
    data_x : pd.Series
        the subset of data containing the dependent variable
    label_encoders : dict
        a dict of label_encoder objects
    """
    if condition:
        len_before = len(data)
        data = data.query(condition)
        if not suppress_print:
            print len(data)
            percent = 100*(len_before - len(data))/len_before
            print ''
            print 'after imposing the condition: {}'.format(condition)
            print 'the dataset was reduced by {:.0f}%'.format(percent)

    # remove cancelled flights from dataset
    idx = data['Cancelled'] == 0
    data = data.loc[idx, :]

    # create Y-variables
    data['Delay'] = data['DepDelayMinutes'] > 15

    # create hour variable
    data['Hour'] = data['DepTime'].apply(lambda s: get_hour(s))

    # make air time an integer
    data['AirTime'] = data['AirTime'].astype(float)

    # Encode categoricals
    label_encoders = {}
    for col in categoricals:
        le = LabelEncoder()
        le.fit(data[col])
        data[col] = le.transform(data[col])
        label_encoders[col] = le

    allcols_data = deepcopy(data)
    data = data[xcols + ['Delay']]

    if not suppress_print:
        # show distribution of null values in data
        for c in data.columns:
            print '{} has {} nulls'.format(c, sum(data[c].isnull()))
        print ''

    len_before = len(data)
    # remove null values
    for c in data.columns:
        idx = data[c].notnull()
        testing.assert_series_equal(idx, allcols_data[c].notnull())

        data = data[idx]
        allcols_data = allcols_data[idx]

    if not suppress_print:
        percent = 100*(len_before - len(data))/len_before
        print 'len before drop nulls: {}'.format(len_before)
        print 'len before drop nulls: {}'.format(len(data))

        print 'After removing nulls dataset reduced by {:.0f}%'.format(percent)
        print ''
        print 'Delay Distribution'
        print data['Delay'].value_counts()
        print ''

    data_y = data['Delay']
    data_x = data[xcols]

    return allcols_data, data_x, data_y, label_encoders


def test_model(mdl, Origin, xcols, categoricals, condition=None, suppress_print=False):
    """train the given model using the training data and predict
    results on the test data and then display the confusion matrix,
    precision, recall, F1 score and accuracy
    """

    store = pd.HDFStore(hdf_path, 'r')
    train_where = ['Year == 2013', "Origin == '{}'".format(Origin)]
    train_data = store.select('flat_file', where=train_where)
    if not suppress_print:
        print 'Get Train data'
        print '--------------'
    train_data, train_x, train_y, train_label_encoders = prep_data(xcols, categoricals, train_data, condition, suppress_print)

    test_where = ['Year == 2014', "Origin == '{}'".format(Origin)]
    test_data = store.select('flat_file', where=test_where)
    if not suppress_print:
        print 'Get Test data'
        print '--------------'
    test_data, test_x, test_y, test_label_encoders = prep_data(xcols, categoricals, test_data, condition, suppress_print)

    mdl.fit(train_x, train_y)
    pr = mdl.predict(test_x)
    cm = confusion_matrix(test_y, pr)
    report = precision_recall_fscore_support(test_y, pr, average='binary')

    # Feature Ranking
    importances = mdl.feature_importances_
    indices = np.argsort(importances)[::-1]

    if not suppress_print:
        print 'Feature Ranking'
        print '---------------'
    cols = []
    scores = []
    for i in xrange(0, len(test_x.columns)):
        col = test_x.columns[indices[i]]
        score = importances[indices[i]]
        if not suppress_print:
            print 'feature {} ({})'.format(col, score)
        cols.append(col)
        scores.append(score)

    if not suppress_print:
        print ''
        print 'Confusion Matrix'
        print '---------------'
        print pd.DataFrame(cm)
        print ' '

    feature_ranks = pd.DataFrame({'Feature': cols, 'Score': scores})

    stats = show_stats(report, accuracy_score(test_y, pr), suppress_print=suppress_print)

    std = np.std([tree.feature_importances_ for tree in mdl.estimators_], axis=0)

    if not suppress_print:
        # Plot the feature importances of the forest
        plt.figure()
        plt.xticks(rotation=45)
        plt.title("Feature importance")
        plt.bar(range(test_x.shape[1]), importances[indices],
            color="r", yerr=std[indices], align="center")
        plt.xticks(range(test_x.shape[1]), train_x.columns[indices])
        plt.xlim([-1, test_x.shape[1]])
        plt.show()

    store.close()

    actual_delays = pd.DataFrame({'Delay Dist': test_y.value_counts(normalize=True)})
    actual_delays.loc['Total', 'Delay Dist'] = len(test_y)

    return feature_ranks, stats, actual_delays

if __name__ == '__main__':

    mdl = RandomForestClassifier(n_estimators=50, n_jobs=-1)

    # a security delay would seem to be harder to predict, but I wonder if it is higher at certain FlightDelays
    # types of delays, u'SecurityDelay'  u'WeatherDelay' u'NASDelay' 'CarrierDelay' 'LateAircraftDelay'

    xcols = [u'DayOfWeek', u'DayofMonth', u'Month', u'UniqueCarrier', u'Dest', u'Distance', u'AirTime',
         u'Hour',]
    weather_origin_cols = [
        u'OriginPRCP', u'OriginSNOW', u'OriginSNWD',
        u'OriginTMAX', u'OriginTMIN'
    ]
    weather_dest_cols = [
        u'DestPRCP', u'DestSNOW', u'DestSNWD',
        u'DestTMAX', u'DestTMIN'
    ]
    weather_cols = weather_origin_cols + weather_dest_cols

    aircraft_cols = [u'Engine Model', u'MFR Year', u'Manufacturer Name',
                         u'Model']

    xcols.extend(weather_cols)
    xcols.extend(aircraft_cols)
    categoricals = ['UniqueCarrier', 'Dest']
    categoricals.extend(aircraft_cols)

    condition = "(Origin_airport_to_station < 10) & (Dest_airport_to_station < 10)"

    Origin = 'JFK'
    store = pd.HDFStore(hdf_path, 'r')
    train_where = ['Year == 2013', "Origin == '{}'".format(Origin)]
    train_data = store.select('flat_file', where=train_where)
    train_data, train_x, train_y, train_label_encoders = prep_data(xcols, categoricals, train_data, condition)

    # Top 5 businest airports in the US by total passenger boardings
    airports = ['ATL', 'LAX', 'ORD', 'DFW', 'JFK']

    all_feature_ranks = pd.DataFrame(index=xrange(0, len(xcols)))
    all_stats = pd.DataFrame(index=['Precision', 'Recall', 'F1','Accuracy'])
    all_actual_delays = pd.DataFrame(index=[0, 1, 'Total'])
    for Origin in airports:
        print Origin

        feature_ranks, stats, actual_delays = test_model(mdl, Origin, xcols, categoricals, condition=condition, suppress_print=True)
        feature_ranks.columns = ['Feature_'+Origin, 'Score_'+Origin]
        stats.columns = [Origin]
        actual_delays.columns = [Origin]

        all_feature_ranks = all_feature_ranks.join(feature_ranks)
        all_stats = all_stats.join(stats)
        all_actual_delays = all_actual_delays.join(actual_delays)



