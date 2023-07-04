'''
module shtripper for conversion of Globus-M plasma pulses files
to the csv files

Created by N. Zhiltsov
Last updated    2019-12-11: Function copied by V.Solokha from
                            https://gitlab.spectraltech.ru/Rezenter/shtRipper
'''

import struct
import matplotlib.pyplot as plt

version_length = 11
size_int = 4
size_double = 8
size_long = 8
encoding = 'cp1251'


def reconstruct_graph(table):
    mask = [512 for i in range(256)]
    graph = [[-1, -1] for i in range(256)]
    prev = 511
    for i in range(256):
        if not table[i] == 255:
            prev = i
            vertex = table[i]
            while True:
                if mask[vertex] == 512:
                    mask[vertex] = prev
                graph[vertex][mask[vertex] != prev] = prev
                prev = vertex + 256
                vertex = table[prev]
                if vertex == prev - 256:
                    exit(3)
                if vertex == 255:
                    break
    graph[255] = graph[prev - 256]
    return graph


def decompress_huffman(compressed):  # (unsigned char* compressed, graph[256])
    size = struct.unpack('i', compressed[511: 511 + size_int])[0]
    table = [511 for i in range(511)]
    for i in range(511):
        table[i] = struct.unpack('B', compressed[i: i + 1])[0]
    graph = reconstruct_graph(table)
    result = [255 for i in range(size)]
    index = 0
    for i in range(size):
        bit = index % 8
        byte = 511 + size_int + (index // 8)
        b = (compressed[byte] & (1 << bit)) != 0
        index += 1
        p_graph = graph[255]
        while p_graph[b] > 255:
            p_graph = graph[p_graph[b] - 256]
            bit = index % 8
            byte = 511 + size_int + (index // 8)
            b = (compressed[byte] & (1 << bit)) != 0
            index += 1
        result[i] = p_graph[b]
    return result


def decompress_rle(comp):
    n_bytes = 0
    i = 0
    result = []
    while True:
        delta = comp[i] & 127
        if (comp[i] & 128) == 0:
            for j in range(delta):
                result.append(comp[i + 1])
            i += 2
        else:
            for j in range(delta):
                result.append(comp[i + 1 + j])
            i += delta + 1
        n_bytes += delta
        if i >= len(comp):
            break
    return result


def change_byte_order(data, data_size):
    level = 4
    res = [0 for i in range(data_size)]
    n0 = 0
    for n in range(level):
        n1 = data_size // level + ((data_size % level) > n)
        for i in range(n1):
            res[i * level + n] = data[n0 + i]
        n0 += n1
    res_int = []
    for i in range(data_size // size_int):
        res_int.append(struct.unpack('i', bytearray(res[i * size_int: (i + 1) * size_int]))[0])
    return res_int


def unpack_struct(pack):
    res = {}
    pos = 0
    res['type'] = struct.unpack('i', bytearray(pack[pos: pos + size_int]))[0]
    pos += size_int
    buff = []
    for c in pack[pos: pos + 128]:
        if c != 0:
            buff.append(c)
    res['name'] = bytearray(buff).decode(encoding)
    pos += 128
    buff = []
    for c in pack[pos: pos + 128]:
        if c != 0:
            buff.append(c)
    res['comm'] = bytearray(buff).decode(encoding)
    pos += 128
    buff = []
    for c in pack[pos: pos + 128]:
        if c != 0:
            buff.append(c)
    res['unit'] = bytearray(buff).decode(encoding)
    pos += 128

    time = struct.unpack('HHHHHHHH', bytearray(pack[pos: pos + 16]))
    res['time'] = {
        'year': time[0],
        'month': time[1],
        'weekDay': time[2],
        'monthDay': time[3],
        'hour': time[4],
        'minute': time[5],
        'second': time[6],
        'mSecond': time[7]
    }
    pos += 16

    res['#ch'] = struct.unpack('i', bytearray(pack[pos: pos + size_int]))[0]
    pos += size_int

    res['tMin'] = struct.unpack('d', bytearray(pack[pos: pos + size_double]))[0]
    pos += size_double

    res['tMax'] = struct.unpack('d', bytearray(pack[pos: pos + size_double]))[0]
    pos += size_double

    res['uMin'] = struct.unpack('d', bytearray(pack[pos: pos + size_double]))[0]
    pos += size_double

    res['delta'] = struct.unpack('d', bytearray(pack[pos: pos + size_double]))[0]
    pos += size_double

    data = []
    while pos < len(pack):
        data.append(struct.unpack('B', bytearray(pack[pos: pos + 1]))[0])
        pos += 1

    data_size = 0
    if res['type'] >> 16 == 0:
        data_size = res['#ch'] * size_int
    elif res['type'] >> 16 == 1:
        data_size = res['#ch'] * size_double * 2
    elif res['type'] >> 16 == 2:
        data_size = res['#ch'] * size_double * 3
    else:
        exit(4)

    res['data'] = change_byte_order(data, data_size)
    return res


def x_y(hist):
    x = []
    y = []
    if hist['type'] >> 16 == 0:
        t_mult = (hist['tMax'] - hist['tMin']) / (hist['#ch'] - 1)
        for i in range(len(hist['data'])):
            x.append(i * t_mult + hist['tMin'])
            y.append(hist['data'][i] * hist['delta'] + hist['uMin'])
    elif hist['type'] >> 16 == 1:
        for i in range(len(hist['data']) // 2):
            x.append(hist['data'][i * 2])
            y.append(hist['data'][i * 2 + 1])
    elif hist['type'] >> 16 == 2:
        for i in range(len(hist['data']) // 3):
            x.append(hist['data'][i * 3])
            y.append(hist['data'][i * 3 + 1])
    return x, y


def plot_hist(hist):
    x, y = x_y(hist)
    plt.plot(x, y)
    plt.title(hist['name'])
    plt.xlabel('time (s)')
    plt.ylabel(hist['unit'])
    plt.show()


def extract(path, shotn, requested=None):
    filename = '%s/sht%d.SHT' % (path, shotn)
    with open(filename, 'rb') as file:
        version_str = file.read(version_length).decode('ascii')
        version = -1
        if version_str[0:8] == 'ANALIZER':
            if version_str[-1] == '0':
                version = 0
            elif version_str[-1] == '1':
                version = 1
            elif version_str[-1] == '2':
                version = 2
            else:
                print("Unknown version of .sht file: %d" % version)
                exit(1)
            print('version = %d' % version)
        else:
            print("Unknown version header of .sht file: '%s'" % version_str)
            exit(1)

        file.seek(1, 1)  # wtf?

        count = struct.unpack('i', file.read(size_int))[0]
        print('count %d' % count)
        if version == 0:
            print('not implemented')
            exit(2)
        elif version == 1:
            print('not implemented')
            exit(2)
        else:
            result = {}
            queue = []
            if requested is None:
                queue = range(count)
            else:
                for item in requested:
                    if 0 <= item < count:
                        queue.append(item)
                    else:
                        print('Requested item %d is out of range [%d, %d)' % (item, 0, count))
            processed = 1
            for l in range(count):
                size = struct.unpack('i', file.read(size_int))[0]
                if size > 0:
                    raw = file.read(size)
                    if l in queue:
                        print('decompressing...')
                        huff = decompress_huffman(raw)
                        result[l] = unpack_struct(decompress_rle(huff))
                        print('decompressed %d of %d' % (processed, len(queue)))
                        processed += 1
            return result