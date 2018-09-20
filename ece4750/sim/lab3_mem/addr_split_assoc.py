#! /usr/bin/env python2

import argparse


def bin32(x):
    return bin(x)[2:].zfill(32)


def numify(thing):
    if thing.startswith('0x'):
        return int(thing, 16)
    elif thing.startswith('0b'):
        return int(thing, 2)
    else:
        return int(thing)


def nhex(x):
    return '0x' + hex(x)[2:].zfill(8)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('banks')
    parser.add_argument('addrs', nargs='+')
    args = parser.parse_args()

    banks = int(args.banks)
    addrs = [bin32(numify(x)) for x in args.addrs]
    for addr in addrs:
        print(nhex(int(addr, 2)))
        if banks == 1:
            tag = int(addr[0:25], 2)
            index = int(addr[25:28], 2)
            offset = int(addr[28:32], 2)
            print('\ttag\t%s\n\tindex\t%s\n\toffset\t%s' %
                  (nhex(tag), nhex(index), nhex(offset)))
        elif banks == 4:
            tag = int(addr[0:23], 2)
            index = int(addr[23:26], 2)
            bank = int(addr[26:28], 2)
            offset = int(addr[28:32], 2)
            print('\ttag\t%s\n\tindex\t%s\n\tbank\t%s\n\toffset\t%s' %
                  (nhex(tag), nhex(index), nhex(bank), nhex(offset)))
        else:
            print('\tBank has to be either 1 or 4, dufus')
        print('')


if __name__ == '__main__':
    main()
