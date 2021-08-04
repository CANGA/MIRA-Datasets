import plotly.express as px
import time
import plotly
import os
import pandas as pd
import numpy as np
from scipy.stats import linregress

from plotly import tools
import chart_studio.plotly as py
import plotly.graph_objs as go

# Global variables
NMETHODS = 4
NDATASETS = 3
NRESOLUTIONS = 5
MetricsFilePath = '../MetricsData/'

# Our reference data resolutions for different grids
METHODS = ['TempestRemap', 'GMLS', 'WLS-ENOR', 'ESMF']
GRIDTYPES = ['CS-MPAS', 'MPAS-RLL', 'RLL-CS']
DATAVARIABLES = ['AnalyticalFun1', 'AnalyticalFun2',
                 'CloudFraction', 'Topography', 'TotalPrecipWater']
CSRES = ['16', '32', '64', '128', '256']
CSELEMS = [1536, 6144, 24576, 98304, 393216]
ICODRES = ['16', '32', '64', '128', '256']
ICODELEMS = [2562, 10242, 40962, 163842, 655362]
RLLRES = ['30-60', '90-180', '180-360', '360-720', '720-1440']
RLLELEMS = [1800, 16200, 64800, 259200, 1036800]

NRRMRESOLUTIONS = 3
RRMCSELEMS = [15858, 112606, 247328]
RRMICODELEMS = [15970, 28535, 67886]

# Supported orders for each method
TR_SUPPORTED_ORDERS = [1, 2, 3, 4]
TR_SUBTYPES = ['', 'CAAS']
GMLS_SUPPORTED_ORDERS = [2, 3, 4, 5]
GMLS_SUBTYPES = ['', 'CAAS', 'Normalized']
WLSENOR_SUPPORTED_ORDERS = [2, 3, 4]
ESMF_SUPPORTED_ORDERS = [1, 2]
ESMF_SUBTYPES = ['conserve1st', 'conserve2nd', 'bilinear']

# Store the metrics names available
METRICSNAMES = ['GC', 'GL1', 'GL2', 'GLinf', 'GMaxE', 'GMinE', 'LMaxL1', 'LMaxL2',
                'LMaxLm', 'LMinL1', 'LMinL2', 'LMinLm', 'H12T', 'H1T', 'H12S', 'H1S']

# Store the reference remap iteration points used in the study for plotting
riter = np.linspace(10, 1000, 100, dtype='int32')
REMAPITERATIONS = np.insert(riter, 0, 1, axis=0)

pd.options.display.float_format = '{:,.15e}'.format


def get_dataset(iMETHOD, GridType, iSRC, iTGT, iVARin, Order, subPath=-1):
    '''
    For a given remap method, src/tgt res, variable and order, return dataset

    Parameters:
    argument1 (int): Description of arg1
    iMETHOD (int): Parameter ranging from 0-3. 0: TempestRemap, 1: GMLS, 2: WLS-ENOR, 3: ESMF
    GridType (int): Parameter ranging from 0-2. 0: CS-ICOD, 1: ICOD-RLL, 2: RLL-CS
    iSRC (int): Parameter ranging from 0-4 indicating the source grid resolution in the grid combo
    iTGT (int): Parameter ranging from 0-4 indicating the target grid resolution in the grid combo
    iVARin (int): Parameter ranging between 0-4 indicating analytical and real sampled fields
    Order (int): Order of the method (iMETHOD)
    subPath (int): If a method has variations of datasets with different properties, expose through a sub-path. Default: -1 (None).

    Returns:
    pandas dataframe: The dataframe containing the metrics data in a Pandas dataframe object
    string: The filename of the dataset that is currently loaded onto the dataframe

    '''
    assert(iMETHOD >= 0 and iMETHOD < NMETHODS)
    assert(GridType >= 0 and GridType < NDATASETS)
    assert(iSRC >= 0 and iSRC < 5)
    assert(iTGT >= 0 and iTGT < 5)
    assert(iVARin >= 0 and iVARin < 5)

    filename = ""
    if iMETHOD == 0:
        assert(Order in TR_SUPPORTED_ORDERS)
        TR_SUBPATH = "UniformlyRefined/TempestRemap/{0}/degree-{1}/".format(
            GRIDTYPES[GridType], Order-1)
        if GridType == 0:
            filename = MetricsFilePath + TR_SUBPATH + "metrics_CS{0}_ICOD{1}_O{2}_{3}".format(
                CSRES[iSRC], ICODRES[iTGT], str(Order), DATAVARIABLES[iVARin])
        elif GridType == 1:
            filename = MetricsFilePath + TR_SUBPATH + "metrics_ICOD{0}_RLL{1}_O{2}_{3}".format(
                ICODRES[iSRC], RLLRES[iTGT], str(Order), DATAVARIABLES[iVARin])
        else:
            filename = MetricsFilePath + TR_SUBPATH + "metrics_RLL{0}_CS{1}_O{2}_{3}".format(
                RLLRES[iSRC], CSRES[iTGT], str(Order), DATAVARIABLES[iVARin])
    elif iMETHOD == 1:
        assert(subPath in [0, 1])
        GMLS_SUBPATHS = ['UniformlyRefined/GMLS',
                         'UniformlyRefined/GMLS-CAAS']
        assert(Order in GMLS_SUPPORTED_ORDERS)
        GMLS_SUBPATH = "{0}/{1}/degree-{2}/".format(
            GMLS_SUBPATHS[subPath], GRIDTYPES[GridType], Order-1)
        if GridType == 0:
            filename = MetricsFilePath + GMLS_SUBPATH + "metrics_CS{0}_ICOD{1}_O{2}_{3}".format(
                CSRES[iSRC], ICODRES[iTGT], str(Order), DATAVARIABLES[iVARin])
        elif GridType == 1:
            filename = MetricsFilePath + GMLS_SUBPATH + "metrics_ICOD{0}_RLL{1}_O{2}_{3}".format(
                ICODRES[iSRC], ICODRES[iTGT], str(Order), DATAVARIABLES[iVARin])
        else:
            filename = MetricsFilePath + GMLS_SUBPATH + "metrics_RLL{0}_CS{1}_O{2}_{3}".format(
                ICODRES[iSRC], CSRES[iTGT], str(Order), DATAVARIABLES[iVARin])
    elif iMETHOD == 2:
        assert(Order in WLSENOR_SUPPORTED_ORDERS)
        WLSENO_SUBPATH = "UniformlyRefined/WLS-ENOR/{0}/degree-{1}/".format(
            GRIDTYPES[GridType], Order)
        if GridType == 0:
            filename = MetricsFilePath + WLSENO_SUBPATH + "metrics_CS{0}_ICOD{1}_p={2}_{3}".format(
                CSRES[iSRC], ICODRES[iTGT], str(Order), DATAVARIABLES[iVARin])
        elif GridType == 1:
            filename = MetricsFilePath + WLSENO_SUBPATH + "metrics_ICOD{0}_RLL{1}_p={2}_{3}".format(
                ICODRES[iSRC], CSRES[iTGT], str(Order), DATAVARIABLES[iVARin])
        else:
            filename = MetricsFilePath + WLSENO_SUBPATH + "metrics_RLL{0}_CS{1}_p={2}_{3}".format(
                CSRES[iSRC], CSRES[iTGT], str(Order), DATAVARIABLES[iVARin])
    elif iMETHOD == 3:
        ESMF_METHODS = ['conserve', 'conserve2nd']
        assert(Order in ESMF_SUPPORTED_ORDERS)
        ESMF_METHOD = ESMF_METHODS[Order-1]
        ESMF_SUBPATH = "UniformlyRefined/ESMF/{0}/{1}/".format(
            GRIDTYPES[GridType], ESMF_METHOD)
        if GridType == 0:
            filename = MetricsFilePath + ESMF_SUBPATH + "metrics_CS{0}_ICOD{1}_{2}_{3}".format(
                CSRES[iSRC], ICODRES[iTGT], ESMF_METHOD, DATAVARIABLES[iVARin])
        elif GridType == 1:
            filename = MetricsFilePath + ESMF_SUBPATH + "metrics_ICOD{0}_RLL{1}_{2}_{3}".format(
                ICODRES[iSRC], CSRES[iTGT], ESMF_METHOD, DATAVARIABLES[iVARin])
        else:
            filename = MetricsFilePath + ESMF_SUBPATH + "metrics_RLL{0}_CS{1}_{2}_{3}".format(
                CSRES[iSRC], CSRES[iTGT], ESMF_METHOD, DATAVARIABLES[iVARin])

    else:
        return None, ""

    filename += '.csv'
    compression_context = False
    data = None
    if not compression_context:
        if (os.path.exists(filename+'.bz2')):
            filename += '.bz2'
            data = pd.read_csv(filename, compression='infer')
        elif (os.path.exists(filename)):
            data = pd.read_csv(filename)
        else:
            print('Could not find ', filename)
    else:
        data = pd.read_csv(filename)

    if data is None:
        print('Unable to get dataset. Returning...')
    else:
        # data.head()
        # print("Reading filename: %s"%filename)
        data = data.drop(data.index[0])

    return data, filename


def get_rrm_dataset(iMETHOD, iSRC, iTGT, iVARin, Order, subPath=-1):
    '''
    For a given remap method, src/tgt res, variable and order, return dataset

    Parameters:
    argument1 (int): Description of arg1
    iMETHOD (int): Parameter ranging from 0-3. 0: TempestRemap, 1: GMLS, 2: WLS-ENOR, 3: ESMF
    GridType (int): Parameter ranging from 0-2. 0: CS-ICOD, 1: ICOD-RLL, 2: RLL-CS
    iSRC (int): Parameter ranging from 0-4 indicating the source grid resolution in the grid combo
    iTGT (int): Parameter ranging from 0-4 indicating the target grid resolution in the grid combo
    iVARin (int): Parameter ranging between 0-4 indicating analytical and real sampled fields
    Order (int): Order of the method (iMETHOD)
    subPath (int): If a method has variations of datasets with different properties, expose through a sub-path. Default: -1 (None).

    Returns:
    pandas dataframe: The dataframe containing the metrics data in a Pandas dataframe object
    string: The filename of the dataset that is currently loaded onto the dataframe

    '''
    assert(iMETHOD >= 0 and iMETHOD < NMETHODS)
    assert(iSRC >= 0 and iSRC < 3)
    assert(iTGT >= 0 and iTGT < 3)
    assert(iVARin >= 0 and iVARin < 5)

    filename = ""
    if iMETHOD == 0:
        assert(Order in TR_SUPPORTED_ORDERS)
        TR_SUBPATH = "RegionallyRefined/TempestRemap/degree-{0}/".format(
            Order-1)
        filename = MetricsFilePath + TR_SUBPATH + "metrics_cs{0}_icodr{1}_O{2}_{3}".format(
            CSRES[1+iSRC], iTGT+3, str(Order), DATAVARIABLES[iVARin])

    elif iMETHOD == 1:
        assert(subPath in [0, 1])
        GMLS_SUBPATHS = ['RegionallyRefined/GMLS',
                         'RegionallyRefined/GMLS-CAAS']
        assert(Order in GMLS_SUPPORTED_ORDERS)
        GMLS_SUBPATH = "{0}/degree-{1}/".format(
            GMLS_SUBPATHS[subPath], Order-1)
        filename = MetricsFilePath + GMLS_SUBPATH + "metrics_CS{0}_ICOD{1}_O{2}_{3}".format(
            CSRES[1+iSRC], ICODRES[1+iTGT], str(Order), DATAVARIABLES[iVARin])

    elif iMETHOD == 2:
        assert(Order in WLSENOR_SUPPORTED_ORDERS)
        WLSENO_SUBPATH = "RegionallyRefined/WLS-ENOR/degree-{0}/".format(Order)
        filename = MetricsFilePath + WLSENO_SUBPATH + "metrics_RRMr{0}_MPAS{1}_p={2}_{3}".format(
            CSRES[iSRC], ICODRES[iTGT], str(Order), DATAVARIABLES[iVARin])

    elif iMETHOD == 3:
        ESMF_METHODS = ['conserve', 'conserve2nd']
        assert(Order in ESMF_SUPPORTED_ORDERS)
        ESMF_METHOD = ESMF_METHODS[Order-1]
        ESMF_SUBPATH = "RegionallyRefined/ESMF/{0}/".format(ESMF_METHOD)
        filename = MetricsFilePath + ESMF_SUBPATH + "metrics_cs{0}_icodr{1}_{2}_{3}".format(
            CSRES[1+iSRC], iTGT+3, ESMF_METHOD, DATAVARIABLES[iVARin])

    else:
        return None, ""

    filename += '.csv'
    compression_context = False
    if not compression_context:
        if (os.path.exists(filename+'.bz2')):
            filename += '.bz2'
            data = pd.read_csv(filename, compression='infer')
        elif (os.path.exists(filename)):
            data = pd.read_csv(filename)
        else:
            print('Could not find ', filename)
            filename = ''
            data = []
    else:
        data = pd.read_csv(filename)

    data = data.drop(data.index[0])

    # print("Reading filename: %s"%filename)
    return data, filename


def plot_dataset(
        ivar, metricnames, resolutions=[(0, 0),
                                        (2, 2),
                                        (4, 4),
                                        (0, 4),
                                        (4, 0)],
        gridtypes=[0, 1, 2],
        orders=[4, 4, 4, 2],
        isRRM=False,
        baseImagepath="images",
        showPlot=False):

    ##
    # METHODS # 0: TempestRemp, 1: GMLS, 2: WLS-ENOR, 3: ESMF
    # GRIDTYPES # 0: CS-ICOD, 1: ICOD-RLL, 2: RLL-CS
    ##

    cwd = os.curdir

    for isrc, itgt in resolutions:

        for gridtype in gridtypes if not isRRM else [0]:

            if not isRRM:
                dfTR, filename = get_dataset(
                    0, gridtype, isrc, itgt, ivar, Order=orders[0])

                dfGMLS, filename = get_dataset(
                    1, gridtype, isrc, itgt, ivar, Order=orders[1], subPath=0)

                dfGMLSCAAS, filename = get_dataset(
                    1, gridtype, isrc, itgt, ivar, Order=orders[1], subPath=1)

                dfWLSENO, filename = get_dataset(
                    2, gridtype, isrc, itgt, ivar, Order=orders[2])

                dfESMF, filename = get_dataset(
                    3, gridtype, isrc, itgt, ivar, Order=orders[3])
            else:

                dfTR, filename = get_rrm_dataset(
                    0, isrc, itgt, ivar, Order=orders[0])

                dfGMLS, filename = get_rrm_dataset(
                    1, isrc, itgt, ivar, Order=orders[1], subPath=0)

                dfGMLSCAAS, filename = get_rrm_dataset(
                    1, isrc, itgt, ivar, Order=orders[1], subPath=1)

                dfWLSENO, filename = get_rrm_dataset(
                    2, isrc, itgt, ivar, Order=orders[2])

                dfESMF, filename = get_rrm_dataset(
                    3, isrc, itgt, ivar, Order=orders[3])

            vargridtext = "{0} - {1}".format(
                DATAVARIABLES[ivar], GRIDTYPES[gridtype])

            titledata = {'GC':     r"$\texttt{Global conservation: %s}$" % (vargridtext),
                         'GL1':    r"$L_1 \texttt{ Error Metric: %s}$" % (vargridtext),
                         'GL2':    r"$L_2 \texttt{ Error Metric: %s}$" % (vargridtext),
                         'GLinf':  r"$L_\infty \texttt{ Error Metric: %s}$" % (vargridtext),
                         'GMaxE':  r"$L_{\infty} \texttt{ of Global Maxima: %s}$" % (vargridtext),
                         'GMinE':  r"$L_{\infty} \texttt{ of Global Minima: %s}$" % (vargridtext),
                         'LMaxL1': r"$L_1 \texttt{ Local Maxima: %s}$" % (vargridtext),
                         'LMaxL2': r"$L_2 \texttt{ Local Maxima: %s}$" % (vargridtext),
                         'LMinL1': r"$L_1 \texttt{ Local Minima: %s}$" % (vargridtext),
                         'LMinL2': r"$L_2 \texttt{ Local Minima: %s}$" % (vargridtext),
                         'LMaxLm': r"$L_\infty \texttt{ Local Maxima: %s}$" % (vargridtext),
                         'LMinLm': r"$L_\infty \texttt{ Local Minima: %s}$" % (vargridtext),
                         'H12T':   r"$H_{0.5,T} \texttt{ Gradient Error Metric: %s}$" % (vargridtext),
                         'H1T':    r"$H_{1,T} \texttt{ Gradient Error Metric: %s}$" % (vargridtext),
                         'H12S':   r"$H_{0.5,S} \texttt{ Gradient Error Metric: %s}$" % (vargridtext),
                         'H1S':    r"$H_{1,S} \texttt{ Gradient Error Metric: %s}$" % (vargridtext),
                         }

            yaxisdata = {'GC':     r'$\texttt{Global Field Integral}$',
                         'GL1':    r'$L_1 \texttt{ Global Error}$',
                         'GL2':    r'$L_2 \texttt{ Global Error}$',
                         'GLinf':  r'$L_{\infty} \texttt{ Global Error}$',
                         'GMaxE':  r'$L_{\infty} \texttt{ of Global Field Maxima}$',
                         'GMinE':  r'$L_{\infty} \texttt{ of Global Field Minima}$',
                         'LMaxL1': r'$L_1 \texttt{ of Local Field Maxima}$',
                         'LMaxL2': r'$L_2 \texttt{ of Local Field Maxima}$',
                         'LMaxLm': r'$L_{\infty} \texttt{ of Local Field Maxima}$',
                         'LMinL1': r'$L_1 \texttt{ of Local Field Minima}$',
                         'LMinL2': r'$L_2 \texttt{ of Local Field Minima}$',
                         'LMinLm': r'$L_{\infty} \texttt{ of Local Field Minima}$',
                         'H12T':   r'$H_{0.5,T} \texttt{ Gradient Error on Target}$',
                         'H1T':    r'$H_{1,T} \texttt{ Gradient Error on Target}$',
                         'H12S':   r'$H_{0.5,S} \texttt{ Gradient Error on Source}$',
                         'H1S':    r'$H_{1,S} \texttt{ Gradient Error on Source}$'}

            for metricvar in metricnames:
                fig = go.Figure()
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    # title_text=titledata[metricvar],
                    # title_x=0.5,
                    # title_xanchor='center',
                    # title_yanchor='top',
                    # title_font_family="Times New Roman",
                    xaxis_title="<b>{0}</b>".format(
                        r'$\texttt{Remap Iterations}$'),
                    yaxis_title="<b>{0}</b>".format(yaxisdata[metricvar]),
                    legend_title="<b>Remapping Schemes</b>",
                    showlegend=True,
                    # legend_y=0.5,
                    # legend_yanchor='middle',
                    width=800,
                    height=500,
                    font=dict(
                        family="Courier New, monospace",
                        size=14,
                        color="#7f7f7f"
                    )
                    #      yaxis_type="log"
                )

                print('Computing plots for ', titledata[metricvar])

                def transformvar(metricvec):
                    # if metricvar in ['GC', 'GL1', 'GL2', 'GLinf', 'H12T', 'H1T', 'H12S', 'H1S', 'LMaxL1', 'LMaxL2', 'LML1', 'LMinL2']:
                    if metricvar in ['GC', 'GL1', 'GL2', 'GLinf', 'H12T', 'H1T', 'H12S', 'H1S']:
                        return np.log10(np.abs(metricvec))
                    elif metricvar in ['LMaxL1', 'LMaxL2', 'LMaxLm', 'LMinL1', 'LMinL2', 'LMinLm']:
                        return (metricvec)
                    else:
                        return metricvec

                fig.add_trace(
                    go.Scatter(
                        x=REMAPITERATIONS, y=transformvar(dfTR[metricvar]),
                        mode='lines+markers', name="<b>{0}(p={1})</b>".format(METHODS[0],
                                                                              orders[0]-1)))
                fig.add_trace(
                    go.Scatter(
                        x=REMAPITERATIONS, y=transformvar(
                            dfGMLSCAAS[metricvar]),
                        mode='lines+markers', name="<b>{0}-CAAS(p={1})</b>".format(METHODS[1],
                                                                                   orders[1])))
                fig.add_trace(
                    go.Scatter(
                        x=REMAPITERATIONS, y=transformvar(dfWLSENO[metricvar]),
                        mode='lines+markers', name="<b>{0}(p={1})</b>".format(METHODS[2],
                                                                              orders[2])))
                # fig.add_trace( go.Scatter(x=REMAPITERATIONS, y=transformvar(dfWLSENOC[metricvar]), mode='lines+markers', name="<b>{0}-C({1})</b>".format(METHODS[2],orders[2]))) #, row=1, col=1)
                fig.add_trace(
                    go.Scatter(
                        x=REMAPITERATIONS, y=transformvar(dfESMF[metricvar]),
                        mode='lines+markers', name="<b>{0}(conserve2nd)</b>".format(METHODS[3])))  # , row=1, col=1)

                if showPlot:
                    fig.show()
                else:
                    if not isRRM:
                        sfilename = "{0}/{1}_{2}_{3}_{4}-{5}.png".format(
                            baseImagepath,
                            metricvar, DATAVARIABLES[ivar],
                            GRIDTYPES[gridtype],
                            isrc, itgt)
                    else:
                        sfilename = "{0}/RRM-{1}_{2}_CSr{3}-MPASr{4}.png".format(
                            baseImagepath,
                            metricvar, DATAVARIABLES[ivar],
                            isrc, itgt)
                    print("Saving file: {0}/{1}".format(cwd, sfilename))
                    fig.write_image(sfilename)


def main():

    # Uniform mesh plots for the paper
    plot_dataset(ivar=4, metricnames=['GC'], resolutions=[(0, 4), (4, 0), (4, 4)],
                 gridtypes=[0], orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=2, metricnames=['GMaxE'], resolutions=[(0, 4), (4, 0), (4, 4)],
                 gridtypes=[1], orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=3, metricnames=['GMinE'], resolutions=[(0, 4), (4, 0), (4, 4)],
                 gridtypes=[0], orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=4, metricnames=['LMaxL2'], resolutions=[(0, 4), (4, 0), (4, 4)],
                 gridtypes=[0], orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=3, metricnames=['LMinL2'], resolutions=[(0, 4), (4, 0), (4, 4)],
                 gridtypes=[2], orders=[4, 4, 4, 2], showPlot=False)

    # RRM plots for the paper
    plot_dataset(ivar=3, metricnames=['GC'], resolutions=[(0, 2), (2, 0), (2, 2)], isRRM=True,
                 orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=2, metricnames=['GMaxE'], resolutions=[(0, 2), (2, 0), (2, 2)], isRRM=True,
                 orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=3, metricnames=['LMaxL2'], resolutions=[(2, 2)], isRRM=True,
                 gridtypes=[0], orders=[4, 4, 4, 2], showPlot=False)
    plot_dataset(ivar=3, metricnames=['LMinL2'], resolutions=[(2, 2)], isRRM=True,
                 gridtypes=[0], orders=[4, 4, 4, 2], showPlot=False)


if __name__ == "__main__":
    main()
