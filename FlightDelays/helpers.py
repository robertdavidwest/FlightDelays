__author__ = 'rwest'
import pandas as pd
import numpy as np


def get_hour(s):
    """Get hour from string in format '1224'
    """
    keep_digits = min(2, len(s))

    try:
        hour = int(s[:-keep_digits])
    except:
        hour = np.nan

    # recode [0, 1, 2 , 3] as [24, 25, 26, 27]
    if hour in [0, 1, 2 ,3]:
        hour += 24
    return hour


def show_stats(report, accuracy_score, suppress_print=False):
    """Print precision, recall, F1 and accuracy"""
    if not suppress_print:
        print 'Precision: {:.2f}'.format(report[0])
        print 'Recall: {:.2f}'.format(report[1])
        print 'F1: {:.2f}'.format(report[2])
        print 'Accuracy: {:.2f}'.format(accuracy_score)

    stats = pd.DataFrame({'value': [report[0],
                                   report[1],
                                   report[2],
                                   accuracy_score]},
                         index=['Precision',
                               'Recall',
                               'F1',
                               'Accuracy'])
    return stats



def fix_for_hdf(df):
    """any unicode objects will be converted to strings and any integers to
     floats. and as such can then be saved to hdf"""
    types = df.dtypes
    for col in types[types=='object'].index:
        df[col] = df[col].astype(str)

    for col in types[types=='int64'].index:
        df[col] = df[col].astype(np.float64)

    return df