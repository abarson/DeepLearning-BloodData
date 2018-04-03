"""
command line app for train/testing models.
"""

import argparse
import sys
import os

import we_panic_utils.basic_utils as basic_utils
from we_panic_utils.nn.data_load.train_test_split_csv import train_test_split_with_csv_support


def parse_input():
    """
    parse the input to the script
    
    ### should add --
        -- test_percent : float -- percentage testing set
        -- val_percent : float -- percentage validation set
    
    args:
        None

    returns:
        parser : argparse.ArgumentParser - the namespace containing 
                 all of the relevant arguments
    """

    parser = argparse.ArgumentParser(description="a suite of commands for running a model")

    parser.add_argument("model_type",
                        help="the type of model to run",
                        type=str,
                        choices=["CNN+LSTM", "3D-CNN"])
    
    parser.add_argument("data",
                        help="director[y|ies] to draw data from",
                        type=str,
                        nargs="+")
    
    parser.add_argument("--partition_csv",
                        help="csv containing the mapping from partition paths to heart rate/resp rates",
                        type=str,
                        default="reg_part_out.csv")

    parser.add_argument("--csv",
                        help="csv containing labels subject -- trial -- heart rate -- resp rate",
                        type=str,
                        default="NextStartingPoint.csv")

    parser.add_argument("--train",
                        help="states whether the model should be trained",
                        # type=bool,
                        default=False,
                        action="store_true")

    parser.add_argument("--test",
                        help="states whether the model should be tested",
                        # type=bool,
                        default=False,
                        action="store_true")

    parser.add_argument("--batch_size",
                        help="size of batch",
                        type=int,
                        default=4)

    parser.add_argument("--epochs",
                        help="if training, the number of epochs to train for",
                        type=int,
                        default=100)

    parser.add_argument("--output_dir",
                        help="the output directory",
                        type=str,
                        default="outputs")
    
    parser.add_argument("--input_dir",
                        help="the input directory when testing model",
                        type=str,
                        default=None)

    parser.add_argument("--width_shift_range",
                        help="the range to shift the width",
                        type=float,
                        default=0.0)

    parser.add_argument("--height_shift_range",
                        help="the range to shift the height",
                        type=float,
                        default=0.0)

    parser.add_argument("--zoom_range",
                        help="the range to zoom",
                        type=float,
                        default=0.0)
    
    parser.add_argument("--shear_range",
                        help="the range to shear",
                        type=float,
                        default=0.0)

    parser.add_argument("--vertical_flip",
                        help="flip the vertical axis",
                        default=False,
                        action="store_true")
    
    parser.add_argument("--horizontal_flip",
                        help="flip the horizontal axis",
                        default=False,
                        action="store_true")

    return parser


def summarize_arguments(args):
    """
    report the arguments passed into the app
    
    still TODO
    """
    formatter = "[%s] %s"

    print(formatter % ("model_type", args.model_type))
    print(formatter % ("data", args.data))
    print(formatter % ("partition_csv", args.partition_csv))
    print(formatter % ("csv", args.csv))

    formatter = "[%s] %r"

    print(formatter % ("train", args.train))
    print(formatter % ("test", args.test))

    formatter = "[%s] %d"

    print(formatter % ("batch_size", args.batch_size))
    print(formatter % ("epochs", args.epochs))
    print(formatter % ("rotation_range"))


class ArgumentError(Exception):
    """
    custom exception to thrown due to bad parameter input
    """
    pass


def generate_output_directory(output_dirname):
    """
    create an output directory that contains looks like this:
    
    output_dirname/
        models/
    
    args:
        output_dirname : string - the ouput directory name
    
    returns:
        output_dir : string - name of output_directory
    """

    model_dir = os.path.join(output_dirname, "models")

    basic_utils.basics.check_exists_create_if_not(output_dirname)
    basic_utils.basics.check_exists_create_if_not(model_dir)

    return output_dirname


def verify_directory_structure(dirname):
    """
    verify that the directory provided conforms to a structure
    that looks like this:

    dir_name/
        models/
        train.csv
        validation.csv
        test.csv
    
    args:
        dirname : string - directory in question

    returns:
        verified : bool - whether or not this directory structure
                          is satisfactory 
    """
    
    verified = True

    if os.path.isdir(dirname):
        if not os.path.isdir(os.path.join(dirname, "models")):
            print("[verify_directory_structure] - no %s/models/ directory" % dirname)
            verified = False
        
        if not os.path.exists(os.path.join(dirname, "train.csv")):
            print("[verify_directory_structure] - no %s/train.csv" % dirname)
            verified = False

        if not os.path.exists(os.path.join(dirname, "validation.csv")):
            print("[verify_directory_structure] - no %s/validation.csv" % dirname)
            verified = False

        if not os.path.exists(os.path.join(dirname, "test.csv")):
            print("[verify_directory_structure] - no %s/test.csv" % dirname)
            verified = False

        return verified

    else:
        return False
    

def validate_arguments(args):
    """
    validate the arguments provided, handle bad/incomplete input

    args:
        args - the arguments provided to the script throught parse_input

    returns:
        regular : str - path to the "regular" data directory
        augmented : str - path to the "augmented" data directory
        csv : str - path to filtered_csv
        partitions_csv : str - the path to to the label data
        batch_size : int - batch size
        epochs : int - epochs to train for, if necessary
        train : bool - whether or not to train
        test : bool - whether or not to test
        input_dir : str - the path to the directory containing post experiment/training meta data and results
        output_dir : str - the path to the directory where we will place experimental meta data and results
    """
    for data_dir in args.data:
        if not os.path.isdir(data_dir):
            raise ArgumentError("Bad data directory : %s" % data_dir)
    
    regular, augmented = None, None

    if len(args.data) > 1:
        assert len(args.data) == 2, "Expected maximum two directories, regular and augmented; got %d" % len(args.data)
        print("[validate_arguments] : taking %s to be `regular`, %s to be `augmented`" % (args.data[0], args.data[1]))
        augmented = args.data[1]
        
    regular = args.data[0]

    # if --test=False and --train=False, exit because there's nothing to do
    if (not args.train) and (not args.test):
        raise ArgumentError("Both --train and --test were provided as False " +
                            "exiting because there's nothing to do ...")

    # if batch_size was provided to be negative, exit for bad input
    if args.batch_size < 0:
        raise ArgumentError("The --batch_size should be > 0; " +
                            "got %d" % args.batch_size)
    
    batch_size = args.batch_size

    # if epochs was provided to be negative, exit for bad input
    if args.epochs < 0:
        raise ArgumentError("The --epochs should be > 0; " +
                            "got %d" % args.epochs)
   
    epochs = args.epochs

    # if --test was provided only
    if args.test and not args.train:
        # if no input directory specified, exit for bad input
        if args.input_dir is None:
            raise ArgumentError("--test was specified but found no input " +
                                "directory, provide an input directory to " +
                                "test a model only")
        
        # an input directory was specified but if doesn't exist
        if not os.path.isdir(args.input_dir):
            raise ArgumentError("Cannot find input directory %s" % args.input_dir)

        # verify input directory structure
        if not verify_directory_structure(args.input_dir):
            raise ArgumentError("Problems with directory structure of %s" % args.input_dir)
        
        # verified everythign works, now erase the output directory because the input is the output
        print("[validate_arguments] : overwriting output directory from %s to %s" % (args.output_dir, args.input_dir))
        args.output_dir = args.input_dir

    # if --test=True and --train=True, then we need only an output directory
    if args.train and args.test:
        generate_output_directory(args.output_dir)
        print("[validate_arguments] : overwriting input directory from %s to %s" % (args.input_dir, args.output_dir))
        args.input_dir = args.output_dir
        
    input_dir, output_dir = args.input_dir, args.output_dir
    
    assert os.path.exists(args.csv), "%s not found" % args.csv
    assert os.path.exists(args.partition_csv), "%s not found" % args.partition_csv
 
    return regular, augmented, args.csv, args.partition_csv, batch_size, epochs, args.train, args.test, input_dir, output_dir 


if __name__ == "__main__":
    
    args = parse_input().parse_args()

    regular, augmented, filtered_csv, partition_csv, batch_size, epochs, train, test, inputs, outputs = validate_arguments(args)
    training_paths2labels, testing_paths2labels, validation_paths2labels = train_test_split_with_csv_support(regular, filtered_csv,
                                                                                                             partition_csv, outputs,
                                                                                                             augmented_data_path=augmented)
    
    sys.exit("under construction ... ")
