import sys, argparse
from ProducerAgent.Utils.Validation import validate_path

def main():
    run(parse_args())

def run(args):
    try:
        verbosity = args.verbose
        logger.setLevel(verbosity)
        logger.info('Verbosity set to display info messages.')
        logger.debug('Verbosity set to display debug messages.')

        data_path = validate_path(args.data)
        yaml_path = validate_path(args.yaml)
        if (args.distiller):
            distiller_path = validate_path(args.distiller)
        elif (True):
            #distiller_path = validate_path(ENVVAR)
        else:
            raise Exception('Distiller unspecified')

        #data_collector = DataCollector(path)
        #load = Thread(target=process_file, args=(data_collector,), daemon=True)
        #load.start()




def parse_args():
    parser = argparse.ArgumentParser(description='CLI for Producer.')
    args = parser.add_argument_group('Core parameters')
    argsadd_argument('-v', '--verbose', type=int, required=False, default=30, nargs='?',
                                const=20, help='Set the verbosity level, 20 for INFO, 10 for DEBUG. Default is 30: WARN')
    args.add_argument('-m', '--model', help='Specifies the model to be used', required=True, type=str)
    args.add_argument('-d', '--data', help='Specifies the data directory', required=True, type=str)
    args.add_argument('-y', '--yaml', help='Specifly the .yaml file to use', required=True, type=str)
    args.add_argument('-R', '--redis', help='Specifies the redis host ip', required=False, default=None, type=str)
    args.add_argument('-D', '--distiller',help='Specifies the Distiller root directory', required=False, default=None, type=str)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main() or 0)
    