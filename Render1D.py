# Distribute≈çd under the MIT License.
# See LICENSE.txt for details.
#!/usr/bin/env python
#Python script to render 1D data written using SpECTRE in format v2
# This script originated from someone in Summer of 2018.  The format for volume
# data files has changed and we can use as a model the GenerateXdmf.py in spectre/tools
# as a model.  In addition we probably want to make this script compatible with both
# h5py and the python wrappers of SpECTRE H5 functions.  To this end we may want to factor
# even more functions out


import glob
import h5py
import argparse
import sys
import os # Gives the script additional functionality but may be unnesecary
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
try:
    import Tkinter
except ImportError:
    import tkinter as Tkinter

global line
global title
# May Want these to be arrays, may not matter but should see if performance will be
# a big deal.
time = []
coords = []
data = []


def find_extrema_over_data_set(arr):

    '''
    Find max and min over a range of number arrays
    :param arr: the array over which to find the max and min
    This doesn't really work if there are nan valued data pts.
    '''
    # The last statment of the docstring may or may not be true

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

def find_h5_files(file_prefix):
    '''
    Get a list of the h5 files containing the data
    :return list of h5 files containing volume data
    '''
    #TODO

def print_var_names():
    # This will need to be changed to be consistent with .vol files.
    '''
    Print all available variables to screen
    :param args:
    :return: None
    '''
    # The following three lines are possibly unnecesrary
    ############################################
    data_dirs = glob.glob('File*')
    abs_path = os.getcwd()
    os.chdir(abs_path + '/' + data_dirs[0])
    ############################################
    # Process the available H5 files, should probably be factored out
    ############################################
    h5_file_names = glob.glob('*.h5')
    h5files = [h5py.File(h5_file_names[i], 'r')
               for i in range(len(h5_file_names))]
    elements = h5files[0].keys()
    variables = h5files[0][elements[0]].keys()
    variables.remove("connectivity")
    variables.remove("x-coord")
    #############################################
    print("Variables in H5 file:\n[%s]" % ', '.join(map(str, variables)))
    return None


def get_data(var_name):
    # This probably will need to be changed in order to
    # be consitent with the current format of the .vol files.
    '''
    Get the data to be plotted
    #:return: the array of data, coords, and time
    '''
    # As above maybe unnecessary
    data_dirs = glob.glob('File*')
    data_dirs.sort()
    abs_path = os.getcwd()
    for data_dir in data_dirs:
        os.chdir(abs_path + '/' + data_dir)
        h5_file_names = glob.glob('*.h5')
        #for f in h5_file_names:
        #    print(f)
        # The following two lines should probably become:
        # [ h5py.File(file_name, 'r') for file_name in h5_file_names]
        nfiles = len(h5_file_names)
        h5files = [h5py.File(h5_file_names[i], 'r') for file_name in h5_file_names]
        #Maybe arrays instead of lists?
        local_data = []
        local_coords = []
        local_time = 0.0
        # Similar thing here with list comprehension
        for i in range(len(h5files)):
            f = h5files[i]
            if f.attrs['FileFormatVersion'] != 2:
                print("Bad SpECTRE file format given, %s" %
                      f.attrs['FileFormatVersion'])
                sys.exit(1)
            #Everythign below here needs to be fixed
            ##########################################
            elements = f.keys()
            for element_name in elements:
                element = f[element_name]
                local_time = float(element.attrs['Time'])
                local_data = np.concatenate((np.asarray(element[var_name][()]),
                                             np.asarray(local_data)))
                local_coords = np.asarray(np.concatenate((
                    element["x-coord"][()], local_coords)))
        data.append(local_data)
        coords.append(local_coords)
        time.append(local_time)
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
    # These things are mostly fine probably, just clean up and
    # See if anything can be made more efficient
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
        print("Writing animation to file %s.mp4 at %d frames per second" %
              (args['save'], myfps))
        anim.save("%s.mp4" % args['save'], fps=myfps,
                  extra_args=['-vcodec', 'libx264'])
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
        print_var_names()
        sys.exit(0)

    get_data(args['var'])
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
