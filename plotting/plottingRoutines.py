import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

from mpl_toolkits.axes_grid1 import ImageGrid


__all__ = ['plot_subset_of_array', 'plot_avg_and_sem', 'plot_array', 'imshow_array', 'plot_avg_and_comps', 'plot_array_xy']

def plot_subset_of_array(npArray, keep_slices, axis=1):
    plt.figure()
    
    mask = np.ones_like(npArray, dtype=bool)
    for s in keep_slices:
        # need to make a tuple of Ellipses and an int that is the current trace number
        slice_obj = []
        for a in range(npArray.ndim):
            if a is axis:
                slice_obj.append(s)
            else:
                slice_obj.append(Ellipsis)
        mask[tuple(slice_obj)] = False

    plot(ma.masked_array(npArray, mask))

def plot_avg_and_sem(npArray, axis=1):
    mean = npArray.mean(axis=axis)
    sem_plus = mean + stats.sem(npArray, axis=axis)
    sem_minus = mean - stats.sem(npArray, axis=axis)
    
    plt.figure()
    plt.fill_between(np.arange(mean.shape[0]), sem_plus, sem_minus, alpha=0.5)
    plt.plot(mean)

def plot_array(npArray, axis=1, xlim=None, ylim=None, color=None, suppress_labels=True, title=None):

    f = plt.figure()
    f.suptitle(title, fontsize=14)

    num_plots = npArray.shape[axis]
    side = np.ceil(np.sqrt(num_plots))

    if color is not None:
        if not isinstance(color, (list, tuple)):  # did we pass in a list of colors?
            color_list = [color] * num_plots
    else:
        color_list = [None] * num_plots

    assert(len(color_list) == num_plots)
    for current_plot, color in zip(range(1, num_plots+1), color_list):
        plt.subplot(side, side, current_plot)

        # need to make a tuple of Ellipses and an int that is the current plot number
        slice_obj = []
        for a in range(npArray.ndim):
            if a is axis:
                slice_obj.append(current_plot-1)
            else:
                slice_obj.append(Ellipsis)

        if color is None:
            plt.plot(npArray[tuple(slice_obj)])
        else:
            plt.plot(npArray[tuple(slice_obj)], color=color)

        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        else:
            plot_min = np.min(npArray[np.logical_not(np.isnan(npArray))]) * 0.9
            plot_max = np.max(npArray[np.logical_not(np.isnan(npArray))]) * 1.1
            plt.ylim([plot_min,plot_max])
        
        if suppress_labels:
            a = plt.gca()
            a.set_xticklabels([])
            a.set_yticklabels([])

    return f

def plot_array_xy(npArray_x, npArray_y, axis=1, xlim=None, ylim=None):
    # ensure x and y match in dimensions
    if npArray_x.ndim is not npArray_y.ndim:
        temp_x = np.empty_like(npArray_y)
        while npArray_x.ndim is not npArray_y.ndim:
            npArray_x = np.expand_dims(npArray_x, -1)
        temp_x[:] = npArray_x
        
        npArray_x = temp_x

    plt.figure()

    num_plots = npArray_y.shape[axis]
    side = np.ceil(np.sqrt(num_plots))
    for current_plot in range(1, num_plots+1):

        plt.subplot(side, side, current_plot)
    
        # need to make a tuple of Ellipses and an int that is the current plot number
        slice_obj = []
        for a in range(npArray_y.ndim):
            if a is axis:
                slice_obj.append(current_plot-1)
            else:
                slice_obj.append(Ellipsis)

        plt.plot(npArray_x[tuple(slice_obj)], npArray_y[tuple(slice_obj)])

        if xlim is not None:
            plt.xlim(xlim)
        if ylim is not None:
            plt.ylim(ylim)
        else:
            plot_min = np.min(npArray_y[np.logical_not(np.isnan(npArray_y))]) * 0.9
            plot_max = np.max(npArray_y[np.logical_not(np.isnan(npArray_y))]) * 1.1
            plt.ylim([plot_min,plot_max])


def imshow_array(npArray, axis=2, vmax=None, vmin=None, transpose=False, tight_axis=True, suppress_labels=True, title=None):

    f = plt.figure()
    f.suptitle(title, fontsize=14)

    num_plots = npArray.shape[axis]
    side = np.ceil(np.sqrt(num_plots))
    for current_plot in range(1, num_plots+1):

        plt.subplot(side, side, current_plot)
    
        # need to make a tuple of Ellipses and an int that is the current plot number
        slice_obj = []
        for a in range(npArray.ndim):
            if a is axis:
                slice_obj.append(current_plot-1)
            else:
                slice_obj.append(Ellipsis)

        if vmax is None:
            vmax = np.max(npArray[np.logical_not(np.isnan(npArray))]) * 1.1
        if vmin is None:
           vmin = np.min(npArray[np.logical_not(np.isnan(npArray))]) * 0.9

        if transpose:
            plt.imshow(npArray[tuple(slice_obj)].T, vmax=vmax, vmin=vmin)
        else:
            plt.imshow(npArray[tuple(slice_obj)], vmax=vmax, vmin=vmin)
        if tight_axis is True:
            plt.axis('tight')

        if suppress_labels:
            a = plt.gca()
            a.set_xticklabels([])
            a.set_yticklabels([])
    return f

def plot_avg_and_comps(npArray, axis=1):
    plt.figure()
    plt.plot(npArray, alpha=0.25, lw=1)
    plt.plot(npArray.mean(axis=axis), lw=2, color='black')

