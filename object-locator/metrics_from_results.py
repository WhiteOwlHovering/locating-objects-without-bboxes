# Copyright &copyright 2018 The Board of Trustees of Purdue University.
# All rights reserved.
# 
# This source code is not to be distributed or modified
# without the written permission of Edward J. Delp at Purdue University
# Contact information: ace@ecn.purdue.edu
# =====================================================================

import os
import numpy as np
import pandas as pd
import argparse
import ast
from tqdm import tqdm

from . import metrics
from . import utils

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description='Compute metrics from results and GT.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
required_args = parser.add_argument_group('MANDATORY arguments')
optional_args = parser._action_groups.pop()
required_args.add_argument('results',
                    help='Input CSV file with the estimated locations.')
required_args.add_argument('gt',
                    help='Input CSV file with the groundtruthed locations.')
required_args.add_argument('metrics',
                    help='Output CSV file with the metrics '
                         '(MAE, AHD, Precision, Recall...)')
required_args.add_argument('--dataset',
                           type=str,
                           required=True,
                           help='Dataset directory with the images. '
                                'This is used only to get the image diagonal, '
                                'as the worst estimate for the AHD.')
optional_args.add_argument('--radii',
                           type=str,
                           default=range(0, 15 + 1),
                           metavar='Rs',
                           help='Detections at dist <= R to a GT pt are True Positives.')
args = parser.parse_args()


# Prepare Judges that will compute P/R as fct of r and th
judges = [metrics.Judge(r=r) for r in args.radii]

df_results = pd.read_csv(args.results)
df_gt = pd.read_csv(args.gt)

df_metrics = pd.DataFrame(columns=['r',
                                   'precision', 'recall', 'fscore', 'MAHD',
                                   'MAPE', 'ME', 'MPE', 'MAE',
                                   'MSE', 'RMSE', 'r', 'R2'])

for j, judge in enumerate(tqdm(judges)):

    for idx, row_result in df_results.iterrows():
        filename = row_result['filename']
        row_gt = df_gt[df_gt['filename'] == filename].iloc()[0]

        w, h = utils.get_image_size(os.path.join(args.dataset, filename))
        diagonal = math.sqrt(w**2 + h**2)

        judge.feed_count(row_result['count'],
                         row_gt['count'])
        judge.feed_points(ast.literal_eval(row_result['locations']),
                          ast.literal_eval(row_gt['locations']),
                          max_ahd=diagonal)

    df = pd.DataFrame(data=[[judge.r,
                             judge.precision,
                             judge.recall,
                             judge.fscore,
                             judge.mahd,
                             judge.mape,
                             judge.me,
                             judge.mpe,
                             judge.mae,
                             judge.mse,
                             judge.rmse,
                             judge.pearson_corr \
                                 if not np.isnan(judge.pearson_corr) else 1,
                             judge.coeff_of_determination]],
                      columns=['r',
                               'precision', 'recall', 'fscore', 'MAHD',
                               'MAPE', 'ME', 'MPE', 'MAE',
                               'MSE', 'RMSE', 'r', 'R2'],
                      index=[j])
    df.index.name = 'idx'
    df_metrics = df_metrics.append(df)

# Write CSV of metrics to disk
df_metrics.to_csv(args.metrics)

