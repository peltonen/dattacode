"""These routines are for doing typical extracellular (cell-attached) analyses.

The main data structures we use here are XSG dictionaries.  These
contain keys by default that have a collection of meta-data, and one
key for each of the three ephus programs (ephys, acquierer and
stimulator).

We have been inspired by the spike_sort package, but re-implemented
routines to better fit the XSG data structure.  In particular, we have
'detectSpikes' and 'extractSpikes', as well as routines to calculate
spike rate histograms and densities, and plotting a spike raster.

"""
import numpy as np
import matplotlib.pyplot as plt
import copy

from itertools import repeat
from scipy.stats import norm
from scipy.ndimage import convolve1d

__all__ = ['plotRaster', 'makeSTH', 'makeSpikeDensity', 'detectSpikes', 'extractSpikes']

def detectSpikes(orig_xsg, thresh, edge='falling', channel='chan0', filter_trace=False):
    """This function detects spikes in a merged or unmerged XSG
    dictionary containing cell attached-recordings.  It adds a key
    'spikeTimes' to a new copy of the XSG, which is simply an numpy
    array of events indicies (in milliseconds), or a list of such
    arrays in the case of a merged xsg.  Note that this must be a list
    of numpy arrays, instead of a 2d array, because the # of events is
    different in each trial.

    Note that this routine can take different types of optional
    parameters.  Central is 'thresh', which can be either a floating
    point threshold value, an explicit wave that is exactly the same
    size as a single trial.  One can specify a list of such
    thresholds, one for each trial. This list must be the same overall
    length, but entries can mix and match explict waves and single
    numbers.

    By default we're going to detect spikes in channel 0, and there is
    room here to filter the waves before detection (need to implement
    soon).

    :param: - orig_xsg - merged or unmerged xsg containing cell-attached ephys data
    :param: - thresh - a single threshold or list (as specified above)
    :param: - edge - string, one of 'rising' or 'falling'
    :param: - channel - string- specifying which channel to use (must be a 
                        valid key in the 'ephys' sub-dictionary)
    :param: - filter - boolean, pre-filter traces before detection, not implemented
    :returns: - xsg - a copy of orig_xsg, which adds a single array/list of arrays of spike indicies
    """

    assert(edge in ['falling', 'rising'], "Edge must be 'falling' or 'rising'!")
    xsg = copy.deepcopy(orig_xsg)
    #TODO  separate spike detection and save to XSG routine
    # internal function to be used with a map
    def detect(params): 
        trace, thresh, filter_trace, sample_rate = params

        if filter_trace:
            #trace = filterthetrace(trace)
            pass

        # thresh is now a single value or an explicit wave the same size and shape as trace
        # let's just make it explicit
        if type(thresh) is not np.ndarray:
            thresh = np.ones_like(trace) * thresh
        
        if edge == 'rising':
            i, = np.where((trace[:-1] < thresh[:-1]) & (trace[1:] > thresh[1:]))
        if edge == 'falling':
            i, = np.where((trace[:-1] > thresh[:-1]) & (trace[1:] < thresh[1:]))
        return i * 1000.0 / sample_rate
                
    if 'merged' in xsg.keys():
        # important type expectation here --- could be list of floats or a list of expicit ndarrays
        if type(thresh) is not list:  
            thresh = repeat(thresh)
        if type(filter_trace) is not list:
            filter_trace = repeat(filter_trace)

        xsg['spikeTimes'] = map(detect, zip(np.rollaxis(xsg['ephys'][channel], 1, 0), thresh, filter_trace, repeat(xsg['sampleRate'][0])))
    else:
        xsg['spikeTimes'] = detect((xsg['ephys'][channel], thresh, filter_trace, xsg['sampleRate'])) # wrapping here to make it compatible with the zip for a single trial

    return xsg

def extractSpikes(orig_xsg, width=100, energy=False, channel='chan0'):
    """Creates a list of extracted spikes from a merged or unmerged XSG dictionary.
    Note that the dictionary has to have the key 'spikeTimes', which is 
    generated by detectSpikes().  The value of this key is a single numpy array
    with spike loctions in samples (or a list of such arrays).

    Creates a new key 'extractedSpikes' which is a 2d numpy array of
    samples x spikes, centered on threshold crossing.  The width
    parameter is in samples, and with a sampling frequency of 10kH,
    defaults to 1 millisecond.  The parameter 'energy' controls
    weather each extracted trace is normalized by it's total energy.

    This routine could be improved by 1) accounting for spikes at the
    very edges of the trace 2) aligning the spikes to the peak instead
    of the threshold crossing (maybe best done in the spike detection?
    3) baselining or otherwise normalizing for preperation for PCA

    :param: - xsg - a merged or unmerged XSG dictionary with a 'spikeTimes' entry
    :param: - width - optional int, window size in samples, defaults to 1ms at 10kHz samplling rate
    :param: - energy - optional boolean, controls normalizing by energy level
    :param: - channel - which channel to extract spikes from, defaults to 'chan0'
    :returns: - a xsg with the added field 'extractedSpikes', as explained above
    """
    half_width = int(width / 2)
    xsg = copy.deepcopy(orig_xsg)

    def extract(params):
        data, times = params
        extracted_temp = np.zeros((width, len(times)))
        for i, spike in enumerate(times):
            sample = int(spike*10)
            if energy is True:
                extracted_temp[:,i] = data[sample-half_width:sample+half_width] / (np.sqrt(np.sum(np.power(data[sample-half_width:sample+half_width], 2))))
            else:
                extracted_temp[:,i] = data[sample-half_width:sample+half_width]
        return extracted_temp
            
    if 'merged' in orig_xsg.keys():
        xsg['extractedSpikes'] = map(extract, zip(np.rollaxis(xsg['ephys'][channel], 1, 0), [times for times in xsg['spikeTimes']]))
    else:
        xsg['extractedSpikes'] = extract((xsg['ephys'][channel], xsg['spikeTimes']))

    return xsg


def plotRaster(xsg, ax=None, height=1., xlim=['x1','x2']):
    """Creates raster plot from a merged or unmerged XSG dictionary.
    Note that the dictionary has to have the key 'spikeTimes', which is 
    generated by detectSpikes().  The value of this key is a single numpy array
    with spike loctions in samples (or a list of such arrays).

    Note that we plot these based on the size of the traces themselves.
    This works because we split up our acquisitions, but in general, 
    we might want to only plot regions of the raster.  plt.xlim() should
    be able to be used post-hoc for this.

    :param: - xsg - a merged or unmerged XSG dictionary with a 'spikeTimes' entry
    :param: - ax - optional, a matplotlib axis to plot onto
    :param: - height - optional, spacing for the rasters
    :param: - xlim - option, specifies range of time in milliseconds to display
    """
    #TODO modify to take range argument
    if ax is None:
        ax = plt.gca() # otherwise it'll plot on the top figure

    try:
        if type(xsg['spikeTimes']) is list:
            for trial, trace in enumerate(xsg['spikeTimes']):
                plt.vlines(trace, trial, trial+height)
            plt.ylim(len(xsg['spikeTimes']), 0)
            if xlim == ['x1','x2'] or not isinstance(xlim[0], (int,long,float)): 
                plt.xlim(0,float(xsg['ephys']['chan0'].shape[0]) / xsg['sampleRate'][0] * 1000.0)
            else:
                plt.xlim(xlim[0],xlim[1])

        else:
            plt.vlines(xsg['spikeTimes'], 0, height)
            plt.ylim((0,1))
            plt.xlim(0,float(xsg['ephys']['chan0'].shape[0]) / xsg['sampleRate'] * 1000.0)

        plt.xlabel('time (ms)')
        plt.ylabel('trials')

    except:
        print 'No spike times found!'

def makeSTH(orig_xsg, bin_size=1):
    """Creates spike rate histograms from a merged or unmerged XSG dictionary.
    Note that the dictionary has to have the key 'spikeTimes', which is 
    generated by detectSpikes().  The value of this key is a single numpy array
    with spike loctions in samples (or a list of such arrays).

    This routine creates a new key, 'spikeHist' which is a dictionary.
    It contains 4 entries:
       'binCenters'
       'binEdges'
       'counts'
       'rates' - this is simply counts * 1000 / bin_size
       
    If the xsg was unmerged, these values are 1d arrays.  If it was merged, they are 2d (time x trials)

    :param: xsg - - a merged or unmerged XSG dictionary with a 'spikeTimes' entry
    :param: bin_size - optional bin size in milliseconds.  Default to 1ms. 
    :returns: xsg - a copy of the previous XSG, with the 'spikeHist' dictionary added as described above.
    """
    assert('spikeTimes' in orig_xsg.keys(), 'No spike times found!')

    xsg = copy.deepcopy(orig_xsg)
    xsg['spikeHist'] = {}
    if 'merged' in xsg.keys():
        sampleRate = float(xsg['sampleRate'][0])
    else:
        sampleRate = float(xsg['sampleRate'])

    bins = np.arange(0,xsg['ephys']['chan0'].shape[0] / sampleRate * 1000.0, bin_size)
    rate_factor = 1000.0 / bin_size
    
    def makeHist(params):
        spike_time, bins = params
        counts, bin_edges = np.histogram(spike_time, bins)
        bin_centers = 0.5*(bin_edges[1:]+bin_edges[:-1])
        return bin_centers, counts, bin_edges
    
    if 'merged' in xsg.keys():
        temp_hist = map(makeHist, zip([st for st in xsg['spikeTimes']], repeat(bins)))

        xsg['spikeHist']['binCenters'] = np.array([x[0] for x in temp_hist]).T
        xsg['spikeHist']['counts'] = np.array([x[1] for x in temp_hist]).T
        xsg['spikeHist']['binEdges'] = np.array([x[2] for x in temp_hist]).T
        xsg['spikeHist']['rates'] =  xsg['spikeHist']['counts'] * rate_factor

    else:
        temp_hist = makeHist((xsg['spikeTimes'], bins))
        xsg['spikeHist']['binCenters'] = temp_hist[0]
        xsg['spikeHist']['counts'] = temp_hist[1]
        xsg['spikeHist']['binEdges'] = temp_hist[2]
        xsg['spikeHist']['rates'] =  xsg['spikeHist']['counts'] * rate_factor

    xsg['spikeHist']['binSize'] = bin_size
    return xsg

def makeSpikeDensity(orig_xsg, sigma=100):
    """Creates spike rate densities from from a merged or unmerged XSG dictionary.
    Note that the dictionary has to have the key 'spikeHist', which is 
    generated by makeSTH().  The value of this key is a dictionary of binned
    spiked times and associated metadata (see makeSTH() for details).

    The essential thing that this routine does is smooth the rates
    calculated in makeSTH() with a gaussian of a specified width.
    Note that the resolution of the kernel is dependent on the bin
    size, so the best use of this is to bin with a small value (~1ms
    for instance) and then smooth with something larger (~100ms).  The
    sigma size must be equal or larger than the bin size.  Playing
    with different verions of this yields smoothed approximations of
    the rates you get if you bin with a sample size of 1 second.
    
    This routine creates a new key, 'spikeDensity' which is a dictionary.
    It contains 4 entries:
       'binCenters' - centers of binned values
       'rates' - smoothed rates
       'kernel' - calculated kernel for smoothing
       'sigma' - sigma value passed in, in ms.
       
    If the xsg was unmerged, these values are 1d arrays.  If it was merged, they are 2d (time x trials)
    The exception is sigma, which is a single value.

    :param: xsg - - a merged or unmerged XSG dictionary with a 'spikeDensity' entry
    :param: sigma - optional standard deviation of gaussian to smooth with, in milliseconds.
    :returns: xsg - a copy of the previous XSG, with the 'spikeDensity' dictionary added as described above.
    """
    assert(sigma >= orig_xsg['spikeHist']['binSize']) # the resolution of our guassian depends on the bin size

    xsg = copy.deepcopy(orig_xsg)

    edges = np.arange(-3*sigma, 3*sigma, orig_xsg['spikeHist']['binSize'])
    kernel = norm.pdf(edges, 0, sigma)
    kernel *= orig_xsg['spikeHist']['binSize']
    
    xsg['spikeDensity'] = {}
    xsg['spikeDensity']['binCenters'] = xsg['spikeHist']['binCenters'].copy()
    xsg['spikeDensity']['kernel'] = kernel
    xsg['spikeDensity']['sigma'] = sigma

    # actually smooth.  note that we use ndimage's convolve1d, which by default trims the edges
    xsg['spikeDensity']['rates'] = convolve1d(xsg['spikeHist']['rates'].astype(float), kernel, axis=0)

    return xsg
