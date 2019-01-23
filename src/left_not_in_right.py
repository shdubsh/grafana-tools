from sys import argv
import os

if __name__ == '__main__':
    if not os.path.isfile(argv[1]) or not os.path.isfile(argv[2]):
        print('Not enough arguments or file not found.')
        print('Usage: python src/left_not_in_right.py LEFT_FILE RIGHT_FILE')
        exit(1)

    left_index = []
    right_index = []
    with open(argv[1], 'r') as f:
        for line in f.readlines():
            left_index.append(line.strip())

    with open(argv[2], 'r') as f:
        for line in f.readlines():
            right_index.append(line.strip())

    for metric in left_index:
        if metric not in right_index:
            print('{}'.format(metric, argv[2]))
