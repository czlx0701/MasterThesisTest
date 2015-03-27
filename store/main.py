#!/usr/bin/env python
import math
import numpy as np
import matplotlib.pyplot as plt
import pdb

def build_seg_list():
    FILENAME = 'seg_data'
    result = []
    raw_seg_len = []
    with open(FILENAME, 'r') as f:
        for line in f:
            name, time480, size480, name1, time720, size720 = line.split()
            result.append(int(size720) + int(size480))
            raw_seg_len.append((int(size720), int(size480)))
    return result, 2, np.array(raw_seg_len)

def store(nb_stream, clip_size, lb, sigma):
    lc = clip_size.mean()
    M = math.sqrt(sigma * sigma + 4 * lb * lc) - sigma
    M = M / (2 * lc)
    M = int(M * M)
    alpha = 1 + sigma / (lc * math.sqrt(M))

    now_size = 4 # end flag
    now_block = 0
    blocks = 1
    overflow_block = 1
    overflow_size  = 4
    overflow_count = 0
    index = 0
    total_size = 0
    size_index = (nb_stream + 1) * 4 # time (float), offset (int), offset...
    while index < len(clip_size):
        clip = clip_size[index]
        if now_block == M:
            total_size += now_size
            now_block = 0
            now_size  = 4
            blocks   += 1
        now_block += 1
        index += 1
        if now_block == M:
            # last block
            if now_size + size_index + clip <= lb:
                now_size += size_index + clip
                continue
        elif now_size + size_index + clip + 4 <= lb: # space for overflow
            now_size += size_index + clip
            continue
        # overflow
        now_size += 4 # store block index
        index -= 1
        while True:
            overflow_count += 1
            if overflow_size + size_index + clip <= lb:
                # store in current block
                overflow_size += size_index + clip
            else:
                # store in new block
                total_size += overflow_size
                overflow_size = 4 + size_index + clip
                overflow_block += 1
            now_block += 1
            index += 1
            if index >= len(clip_size):
                break
            clip = clip_size[index]
            if now_block > M:
                index -= 1
                now_block = M
                break

    if overflow_size == 4:
        overflow_block -= 1
    else:
        if overflow_size + now_size <= lb:
            overflow_size += now_size
            now_size = 0
        total_size += overflow_size
    if now_size > 4:
        total_size += now_size

    return {
        'M':     M,
        'alpha': alpha,
        'blocks': blocks,
        'overflow': overflow_block,
        '#overflow': overflow_count,
        'total_size': int(total_size),
        # 'count': int(math.ceil(len(clip_size) / M)),
        'ratio': total_size / clip_size.sum()
    }

def build_seg_length(seg_list):
    plt.rc('text', usetex = True)
    plt.rc('font', family = 'Times-Roman', size = 10.5)
    plt.figure(figsize = (6.2, 4))
    # plt.title(title)
    x = np.arange(seg_list.shape[0])
    for stream in range(seg_list.shape[1]):
        plt.plot(x, seg_list[:, stream], label = 'Stream %d' % (stream + 1))
    plt.legend(loc = 'upper right', fontsize = 10.5)
    plt.tight_layout()
    plt.savefig('StoreSegLen.pdf', format = 'pdf')
    print seg_list.sum(axis = 0)

def main():
    Mega = 1024 ** 2
    seg_list, nb_stream, raw_seg_len = build_seg_list()
    clip_size = np.array(seg_list, dtype=float)
    build_seg_length(raw_seg_len)
    avg = clip_size.mean()
    std = clip_size.std()
    total = clip_size.sum()
    print 'mean = %f, std = %f, sum = %d' % (avg, std, int(total))

    print 'block_size\traw_block\tfactor\tM\talpha\tblocks\toverflow_block\toverflow_clip\ttotal_size\tsize_ratio\tblock_ratio'
    for bs in (16, 32, 64, 96, 128):
        # print 'block_size = %dM, min_block = %d' % (bs, math.ceil(total / bs / Mega))
        for factor in range(6):
            best_block = math.ceil(total / bs / Mega)
            result = store(nb_stream = nb_stream, clip_size = clip_size, lb = bs * Mega, sigma = std * factor)
            print '%dMB\t%d\t%d\t%d\t%.3f\t%d\t%d\t%d\t%d\t%.4f\t%.4f' % (
                bs, best_block, factor,
                result['M'], result['alpha'], result['blocks'],
                result['overflow'], result['#overflow'], result['total_size'],
                (result['total_size'] / total) * 100, (result['blocks'] / best_block) * 100
            )

if __name__ == '__main__':
    main()
