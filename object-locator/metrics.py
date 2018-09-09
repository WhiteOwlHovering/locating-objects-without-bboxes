import math

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from sklearn.neighbors import NearestNeighbors
from . import losses

class Judge():
    """
    A Judge computes the following metrics:
        (Location metrics)
        - Precision
        - Recall
        - Fscore
        - Mean Average Hausdorff Distance
        (Count metrics)
        - Mean Error
        - Mean Absolute Error
        - Mean Percent Error
        - Mean Absolute Percent Error
        - Mean Squared Error
        - Root Mean Squared Error
    """

    def __init__(self, r):
        """
        Create a Judge that will compute metrics with a particular r
         (r is only used to compute Precision, Recall, and Fscore).

        :param r: If an estimated point and a ground truth point 
                  are at a distance <= r, then a True Positive is counted.
        """
        # Location metrics
        self.r = r
        self.tp = 0
        self.fp = 0
        self.fn = 0

        # Internal variables
        self._sum_ahd = 0
        self._sum_e = 0
        self._sum_pe = 0
        self._sum_ae = 0
        self._sum_se = 0
        self._sum_ape = 0
        self._n_calls_to_feed_points = 0
        self._n_calls_to_feed_count = 0

    def feed_points(self, pts, gt, max_ahd=np.inf):
        """
        Evaluate the location metrics of one set of estimations.
         This set can correspond to the estimated points and
         the groundtruthed points of one image.
         The TP, FP, FN, Precision, Recall, Fscore, and AHD will be
         accumulated into this Judge.

        :param pts: List of estmated points.
        :param gt: List of ground truth points.
        :param max_ahd: Maximum AHD possible to return if any set is empty. Default: inf.
        """

        if len(pts) == 0:
            tp = 0
            fp = 0
            fn = len(gt)
        else:
            nbr = NearestNeighbors(n_neighbors=1, metric='euclidean').fit(gt)
            dis, idx = nbr.kneighbors(pts)
            detected_pts = (dis[:, 0] <= self.r).astype(np.uint8)

            nbr = NearestNeighbors(n_neighbors=1, metric='euclidean').fit(pts)
            dis, idx = nbr.kneighbors(gt)
            detected_gt = (dis[:, 0] <= self.r).astype(np.uint8)

            tp = np.sum(detected_pts)
            fp = len(pts) - tp
            fn = len(gt) - np.sum(detected_gt)

        self.tp += tp
        self.fp += fp
        self.fn += fn

        # Evaluation using the Averaged Hausdorff Distance
        ahd = losses.averaged_hausdorff_distance(pts, gt,
                                                 max_ahd=max_ahd)
        self._sum_ahd += ahd
        self._n_calls_to_feed_points += 1

    def feed_count(self, estim_count, gt_count):
        """
        Evaluate count metrics for a count estimation.
         This count can correspond to the estimated and groundtruthed count
         of one image. The ME, MAE, MPE, MAPE, MSE, and RMSE will be updated
         accordignly.

        :param estim_count: (positive number) Estimated count.
        :param gt_count: (positive number) Groundtruthed count.
        """

        if estim_count < 0:
            raise ValueError(f'estim_count < 0, got {estim_count}')
        if gt_count < 0:
            raise ValueError(f'gt_count < 0, got {gt_count}')

        e = estim_count - gt_count
        ae = abs(e)
        if gt_count == 0:
            ape = 100*ae
            pe = 100*e
        else:
            ape = 100 * ae / gt_count
            pe = 100 * e / gt_count
        se = e**2

        self._sum_e += e
        self._sum_pe += pe
        self._sum_ae += ae
        self._sum_se += se
        self._sum_ape += ape

        self._n_calls_to_feed_count += 1

    @property
    def me(self):
        """ Mean Error (float) """
        return float(self._sum_e / self._n_calls_to_feed_count)

    @property
    def mae(self):
        """ Mean Absolute Error (positive float) """
        return float(self._sum_ae / self._n_calls_to_feed_count)

    @property
    def mpe(self):
        """ Mean Percent Error (float) """
        return float(self._sum_pe / self._n_calls_to_feed_count)

    @property
    def mape(self):
        """ Mean Absolute Percent Error (positive float) """
        return float(self._sum_ape / self._n_calls_to_feed_count)

    @property
    def mse(self):
        """ Mean Squared Error (positive float)"""
        return float(self._sum_se / self._n_calls_to_feed_count)

    @property
    def rmse(self):
        """ Root Mean Squared Error (positive float)"""
        return float(math.sqrt(self.mse))

    @property
    def mahd(self):
        """ Mean Average Hausdorff Distance (positive float)"""
        return float(self._sum_ahd / self._n_calls_to_feed_points)

    @property
    def precision(self):
        """ Precision (positive float) """
        return float(100*self.tp / (self.tp + self.fp)) \
            if self.tp > 0 else 0

    @property
    def recall(self):
        """ Recall (positive float) """
        return float(100*self.tp / (self.tp + self.fn)) \
            if self.tp > 0 else 0

    @property
    def fscore(self):
        """ F-score (positive float) """
        return float(2 * (self.precision*self.recall /
                          (self.precision+self.recall))) \
            if self.tp > 0 else 0


def make_metric_plots(csv_path, taus, radii, title=''):
    """
    Create a bunch of plots from the metrics contained in a CSV file.

    :param csv_path: Path to a CSV file containing metrics.
    :param taus: Detection thresholds tau.
                 For each of these taus, a precision(r) and recall(r) will be created.
                 The closest to each of these values will be used.
    :param radii: List of values, each with different colors in the scatter plot.
                  Maximum distance to consider a True Positive.
                  The closest to each of these values will be used.
    :param title: (optional) Title of the plot in the figure.
    :return: Dictionary with matplotlib figures.
    """

    dic = {}

    # Data extraction
    df = pd.read_csv(csv_path)

    plt.ioff()

    # ==== Precision and Recall as a function of R, fixing t ====
    for tau in taus:
        # Find closest threshold
        tau_selected = df.th.values[np.argmin(np.abs(df.th.values - tau))]
        print(f'Making Precision(r) and Recall(r) using tau={tau_selected}')

        # Use only a particular r
        precision = df.precision.values[df.th.values == tau_selected]
        recall = df.recall.values[df.th.values == tau_selected]
        r = df.r.values[df.th.values == tau_selected]

        # Create the figure for "Crowd" Dataset
        fig, ax = plt.subplots()
        precision = ax.plot(r, precision, 'r--',label='Precision')
        recall = ax.plot(r, recall,  'b:',label='Recall')
        ax.legend()
        ax.set_ylabel('%')
        ax.set_xlabel(r'$r$ (in pixels)')
        ax.grid(True)
        plt.title(title + f' tau={tau_selected:4f}')

        # Add figure to dictionary
        dic[f'precision_and_recall_vs_r,_tau={tau_selected}'] = fig

    # ==== Precision vs Recall ====
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    if len(radii) > len(colors):
        raise ValueError(f'Too many radii provided, maximum {len(colors)}')

    # Create figure
    fig, ax = plt.subplots()
    plt.ioff()
    ax.set_ylabel('Precision')
    ax.set_xlabel('Recall')
    ax.grid(True)
    plt.title(title)

    for r, c in zip(radii, colors):
        # Find closest R
        r_selected = df.r.values[np.argmin(np.abs(df.r.values - r))]

        # Use only a particular r
        precision = df.precision.values[df.r.values == r_selected]
        recall = df.recall.values[df.r.values == r_selected]

        # Sort by ascending recall
        idxs = np.argsort(recall)
        recall = recall[idxs]
        precision = precision[idxs]

        # Plot precision vs. recall for this r
        ax.scatter(recall, precision, c=c, s=2, label=f'r={r}')

    # Invert legend order
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]
    
    # Put legend outside the plot
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(handles, labels, bbox_to_anchor=(1, 0.5))

    # Add figure to dictionary
    dic['precision_vs_recall'] = fig


    # ==== Precision as a function of tau for all provided R ====
    # Create figure
    fig, ax = plt.subplots()
    plt.ioff()
    ax.set_ylabel('Precision')
    ax.set_xlabel(r'$\tau$')
    ax.grid(True)
    plt.title(title)

    list_of_precisions = []

    for r, c in zip(radii, colors):
        # Find closest R
        r_selected = df.r.values[np.argmin(np.abs(df.r.values - r))]

        # Use only a particular r
        precision = df.precision.values[df.r.values == r_selected]
        list_of_precisions.append(precision)
        taus = df.th.values[df.r.values == r_selected]

        # Plot precision vs tau for this r
        ax.scatter(taus, precision, c=c, s=2, label=f'r={r}')

    ax.plot(taus, np.average(np.stack(list_of_precisions), axis=0),
            'k-', label='avg')

    # Invert legend order
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]

    # Put legend outside the plot
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(handles, labels, bbox_to_anchor=(1, 0.5))

    # Add figure to dictionary
    dic['precision_vs_th'] = fig

    # ==== Recall as a function of tau for all provided R ====
    # Create figure
    fig, ax = plt.subplots()
    plt.ioff()
    ax.set_ylabel('Recall')
    ax.set_xlabel(r'$\tau$')
    ax.grid(True)
    plt.title(title)

    list_of_recalls = []

    for r, c in zip(radii, colors):
        # Find closest R
        r_selected = df.r.values[np.argmin(np.abs(df.r.values - r))]

        # Use only a particular r
        recall = df.recall.values[df.r.values == r_selected]
        list_of_recalls.append(recall)
        taus = df.th.values[df.r.values == r_selected]

        # Plot precision vs tau for this r
        ax.scatter(taus, recall, c=c, s=2, label=f'r={r}')

    ax.plot(taus, np.average(np.stack(list_of_recalls), axis=0),
            'k-', label='avg')

    # Invert legend order
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]

    # Put legend outside the plot
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(handles, labels, bbox_to_anchor=(1, 0.5))

    # Add figure to dictionary
    dic['recall_vs_tau'] = fig


    # ==== F-score as a function of tau for all provided R ====
    # Create figure
    fig, ax = plt.subplots()
    plt.ioff()
    ax.set_ylabel('F-score')
    ax.set_xlabel(r'$\tau$')
    ax.grid(True)
    plt.title(title)

    list_of_fscores = []

    for r, c in zip(radii, colors):
        # Find closest R
        r_selected = df.r.values[np.argmin(np.abs(df.r.values - r))]

        # Use only a particular r
        fscore = df.fscore.values[df.r.values == r_selected]
        list_of_fscores.append(fscore)
        taus = df.th.values[df.r.values == r_selected]

        # Plot precision vs tau for this r
        ax.scatter(taus, fscore, c=c, s=2, label=f'r={r}')

    ax.plot(taus, np.average(np.stack(list_of_fscores), axis=0),
            'k-', label='avg')

    # Invert legend order
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = handles[::-1], labels[::-1]

    # Put legend outside the plot
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(handles, labels, bbox_to_anchor=(1, 0.5))

    # Add figure to dictionary
    dic['fscore_vs_tau'] = fig

    return dic

