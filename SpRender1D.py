# Distributed under the MIT License.
# See LICENSE.txt for details.
#!/usr/bin/env python
#Python script to render 1D SpECTRE Volume Data using Matplotlib

import glob
SPECTRE_LOADED = False
try:
    from spectre import DataStructures
    from spectre.IO import H5 as spectre_h5
    SPECTRE_LOADED = True
except:
    print("Failed loading the SpECTRE python modules. Falling back to h5py,\
    which may have incompatibilities with the file format of the data.")
    import h5py
import argparse
import sys
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
try:
    import Tkinter
except ImportError:
    import tkinter as Tkinter

global line
global title

time = []
coords = []
data = []


def find_extrema_over_data_set(arr):

    '''
    Find max and min over a range of number arrays
    :param arr: the array over which to find the max and min
    This doesn't really work if there are nan valued data pts.
    '''

    return np.nanmin(np.asarray(arr)), np.nanmax(np.asarray(arr))


def init():

    '''
    Initialize the animation canvas
    :return: empty line and title info
    '''

    line.set_data([], [])
    title.set_text("")
    return line, title


def animate(iteration):
    '''
    Update the animation canvas
    '''

    title.set_text("t = %.5f" % time[iteration])
    line.set_data(coords[iteration], data[iteration])
    return line, title


def parse_cmd_line():
    '''
    parse command-line arguments
    :return: dictionary of the command-line args, dashes are underscores
    '''

    parser = argparse.ArgumentParser(description='Render 1-dimensional data',
                                     formatter_class=
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--file-prefix', type=str, required=True,
                        help='common prefix of all h5 files being used \
                        in the case of a single h5 file, it is the file name \
                        without the .h5 extension')
    parser.add_argument('--var', type=str, required=True,
                        help='name of variable to render. eg \'psi\', \
                        \'psi-Error\' or \'psi-Analytic\'')
    parser.add_argument('--time', type=int,required=False,
                        help='if given renders the integer observation step \
                        instead of an animation (optional)')
    parser.add_argument('--save', type=str, required=False,
                        help='set to the name of the output file you want \
                        written. For animations this saves an mp4 file and \
                        for stills a pdf. (optional)')
    parser.add_argument('--fps', type=str, required=False,
                        help='Set the number of frames per second when writing\
                        an animation to disk.(optional)')
    parser.add_argument('--interval', type=str, required=False,
                        help='number of milliseconds (optional)')
    parser.add_argument('--list-vars', type=bool, required=False,
                        help='if true then write list of vars in h5 file \
                        and exit (optional)')
    return vars(parser.parse_args())

def get_h5_and_volfiles(file_prefix):
    '''
    Get a list of the volfiles contained inside of the h5 files as objects
    '''
    h5_file_names = glob.glob(file_prefix + "*.h5")
    h5files  = []
    volfiles = []
    if SPECTRE_LOADED:
        for i, file_name in enumerate(h5_file_names):
            h5files.append(spectre_h5.H5File(file_name, 1)),
            volfiles.append(h5files[i].get_vol('/element_data'))
    else:
        for i, file_name in enumerate(h5_file_names):
            h5files.append(h5py.File(file_name, 'r')),
            volfiles.append(h5files[i]['element_data.vol'])


    return(h5files, volfiles)

def print_var_names(args):

    '''
    Print all available variables to screen
    :param args:
    :return: None
    '''
    file_prefix = args["file_prefix"]
    h5files, volfiles = get_h5_and_volfiles(file_prefix)
    volfile = volfiles[0]
    if SPECTRE_LOADED:
        obs_id_0 = volfile.list_observation_ids()[0]
        grid_names = volfile.list_grids(obs_id_0)
        variables  = volfile.list_tensor_componenets(obs_id, grid_names[0])

    else:
        obs_id_0  = volfile.keys()[0]
        grid_names = volfile[obs_id_0].keys()
        grid = volfile[obs_id_0][grid_names[0]]
        variables = grid.keys()
    variables.remove("connectivity")
    variables.remove("x-coord")
    print("Variables in H5 file:\n[%s]" % ', '.join(map(str, variables)))
    for h5_file in h5files:
        h5_file.close()

    return None


def get_data(args):

    '''
    Get the data to be plotted
    #:return: the array of data, coords, and time
    '''
    file_prefix = args["file_prefix"]
    var_name = args["var"]
    h5files, volfiles  = get_h5_and_volfiles(file_prefix)
    # Get a list of times from the first vol file, sort by time value
    if SPECTRE_LOADED:
        ids_and_times = [(obs_id,(volfiles[0]).get_observation_value(obs_id)) for
          obs_id in (volfiles[0]).list_observation_ids()]
    else:
        ids_and_times = [(obs_id,volfiles[0][obs_id].attrs['observation_value']) for
         obs_id in volfiles[0].keys()]
    ids_and_times.sort(key = lambda pair: pair[1])
    # A dictionary with the id_and_times as keys holds the data for each time
    time_data = {}
    for id_and_time in ids_and_times:
        time_data[id_and_time] = []
        for volfile in volfiles:
            if SPECTRE_LOADED:
                local_data = []
                local_coords = []
                for grid_name in volfile.list_grids(id_and_time[0]):
                    local_data  += list(volfile.get_tensor_component(
                        id_and_time[0], grid_name, var_name))
                    local_coords += list(volfile.get_tensor_component(
                        id_and_time[0], grid_name, 'InertialCoordinates_x'))
                    local_coords_and_data  = zip(local_coords, local_data)
                    time_data[id_and_time] += local_coords_and_data

            else:
                # Using h5py to retrieve data
                Obs_Id_File  = volfile[id_and_time[0]]
                local_data = []
                local_coords = []
                for grid_name in Obs_Id_File.keys():
                    h5_grid = Obs_Id_File[grid_name]
                    local_data += list(h5_grid[var_name])
                    local_coords += list(h5_grid['InertialCoordinates_x'])
                    local_coords_and_data  = zip(local_coords, local_data)
                    time_data[id_and_time] += local_coords_and_data
        # The coordinates need to be in order for plotting purposes
        time_data[id_and_time].sort(key = lambda pair: pair[0])
        time.append(id_and_time[1])
        coords.append([pair[0] for pair in time_data[id_and_time]])
        data.append([pair[1] for pair in time_data[id_and_time]])
    for h5file in h5files:
        h5file.close()
    return None


def render_single_time(args):

    '''
    Renders a single time snap shot
    :param args: the command line arguments
    :return: None
    '''

    plt.xlabel("x")
    plt.ylabel(args['var'])
    plt.title("t = %.5f" % time[int(args['time'])])
    plt.plot(coords[int(args['time'])],
             data[int(args['time'])], 'o')
    if args['save']:
        print("Writing still to file %s.pdf" % args['save'])
        plt.savefig("%s.pdf" % args['save'], transparent=True,
                    format='pdf', bbox_inches='tight')
    else:
        plt.show()
    return None


def render_animation(args):

    '''
    Render an animation of the data
    :param args: the command line arguments
    :return: None
    '''

    fig = plt.figure()
    ax = plt.axes(xlim=(find_extrema_over_data_set(coords)),
                  ylim=(find_extrema_over_data_set(data)))
    global line
    global title
    line, = ax.plot([], [], 'o', lw=2)
    ax.set_xlabel('x')
    ax.set_ylabel(args['var'])
    title = ax.set_title("")
    my_interval = 200
    if args['interval']:
        my_interval = float(args['interval'])
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                   frames=len(time), interval=my_interval)
    if args['save']:
        myfps = 30
        if args['fps']:
            myfps = int(args['fps'])
        print("Writing animation to file %s.mpg at %d frames per second" %
              (args['save'], myfps))
        anim.save(args['save'] + ".mpg" , writer='ffmpeg', codec = 'mpeg2video')

    else:
        def propagate_exceptions(self, exc, val, tb):
            raise exc(val).with_traceback(tb)
        Tkinter.Tk.report_callback_exception = propagate_exceptions
        plt.show()
    return None


def main(args):
    '''
    :param args: command line arguments
    :return: None
    '''

    if args['list_vars']:
        print_var_names(args)
        sys.exit(0)

    get_data(args)
    if args['time']:
        render_single_time(args)
    else:
        render_animation(args)
    return None

if __name__ == "__main__":
    try:
        main(parse_cmd_line())
    except KeyboardInterrupt:
        pass
