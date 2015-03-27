#!/usr/bin/env python
# coding=utf8
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from collections import defaultdict

client, router_in, router = 0, 1, 2
server1, server2, server3, server4 = 3, 4, 5, 6

def link(src, dst):
    return '%s,%s' % (src, dst)

class PacketTracker(object):
    def __init__(self):
        super(PacketTracker, self).__init__()
        default_item = {
            'pkt_sent': 0,
            'pkt_drop': 0,
            'packets':  None,
            'bytes':    0
        }
        links = {
            link(client, router_in): r'$C \rightarrow R$',
            link(router, server1):   r'$R \rightarrow S1$',
            link(router, server2):   r'$R \rightarrow S2$',
            link(router, server3):   r'$R \rightarrow S3$',
            link(router, server4):   r'$R \rightarrow S4$',
        }
        self.links = {}
        for l in links:
            self.links[l] = dict(default_item)
            self.links[l]['packets'] = defaultdict(dict)
            self.links[l]['label'] = links[l]
        self.flows = defaultdict(dict)
        self.highest_packet_id = 0

    def arrive(self, action, time, src, dst, pkt_size, flow_id, pkt_id):
        if pkt_id > self.highest_packet_id:
            self.highest_packet_id = pkt_id
        if src == dst:
            return
        now_link = link(src, dst)
        if now_link in self.links:
            now_link = self.links[now_link]
            packet   = now_link['packets'][pkt_id]
            packet['size'] = pkt_size
            if action == '-':
                now_link['pkt_sent'] += 1
                packet['start'] = time
            elif action == 'r':
                packet['end'] = time
                now_link['bytes'] += pkt_size
            elif action == 'd':
                del now_link['packets'][pkt_id]
                now_link['pkt_drop'] += 1
        if action == 'r' and int(dst) in (server1, server2, server3, server4):
            flow = self.flows[flow_id]
            flow['dst'] = int(dst)
            if not 'packets' in flow:
                flow['packets'] = dict()
            flow['packets'][pkt_id] = {
                'end': time,
                'size': pkt_size
            }

    def calc_throughput(self, packets):
        packet_data = [(pkt['end'], pkt['size']) for pkt in packets.values()]
        packet_data = np.array(packet_data)
        packet_data.sort(axis = 0)
        # start = packet_data[:, 0]
        end   = packet_data[:, 0]
        size  = np.cumsum(packet_data[:, 1])
        throughput = size * 8.0 / end # to bits
        throughput = np.hstack([[0.0], throughput])
        end        = np.hstack([[0.0], end])
        # throughput = throughput[end < 40]
        # end        = end[end < 40]
        max_time = end.max()
        time_axis = np.linspace(0, max_time, num = 10000)
        tp_axis   = np.interp(time_axis, end, throughput)
        return np.vstack([time_axis, tp_axis]), throughput[-1]

    def draw_flow(self, name, *flow_ids):
        print name, flow_ids
        plt.rc('text', usetex = True)
        plt.rc('font', size = 10.5)
        figure = plt.figure(figsize = (6.2, 3))
        for flow_id in flow_ids:
            flow = self.flows[flow_id]
            data = flow['data']
            plt.plot(data[0, :], data[1, :] / 1000000.0, label = flow['label'])
        plt.legend(loc = 'lower right', fontsize = 10.5)
        plt.tight_layout()
        plt.savefig(name, format = 'pdf')

    def draw_plot(self, title, name, *link_names):
        print title, name, link_names
        plt.rc('text', usetex = True)
        #plt.rc('font', family = 'Times-Roman', size = 10.5)
        plt.rc('font', size = 10.5)
        figure = plt.figure(figsize = (6.2, 3))
        # plt.title(title)
        for link_name in link_names:
            item = self.links[link_name]
            data = item['data']
            plt.plot(data[0, :], data[1, :] / 1000000.0, label = item['label'])
        plt.legend(loc = 'lower right', fontsize = 10.5)
        plt.ylim(0, 11)
        # ax=plt.gca()
        # ax.set_ylabel(u'吞吐量($M\!b/s)$')
        plt.tight_layout()
        plt.savefig(name, format = 'pdf')

    def calc_flows(self):
        SERVERS = {
            server1: 'S1',
            server2: 'S2',
            server3: 'S3',
            server4: 'S4',
        }
        flows = {}
        for fid in self.flows:
            flow = self.flows[fid]
            tp, avg_tp = self.calc_throughput(flow['packets'])
            label = '$C \leftarrow %s$' % SERVERS[flow['dst']]
            flows[fid] = {
                'label': label,
                'data':  tp,
                'avg_tp': avg_tp
            }
            print fid, flows[fid]['avg_tp']
        return
        self.flows = flows
        self.draw_flow('flows.pdf', *self.flows.keys())

    def throughput(self):
        links = {}
        for l in self.links:
            data = self.links[l]
            if not len(data['packets']):
                continue
            tp, avg_tp = self.calc_throughput(data['packets'])
            links[l] = {
                'label':  data['label'],
                'data':   tp,
                'avg_tp': avg_tp,
            }
            print l, links[l]['avg_tp']
        self.links = links
        cr = link(client, router_in)
        rs1 = link(router, server1) 
        rs2 = link(router, server2) 
        rs3 = link(router, server3) 
        rs4 = link(router, server4) 
        # data = np.vstack([
        #     self.links[cr]['data'],
        #     self.links[rs1]['data'],
        #     self.links[rs2]['data'],
        #     self.links[rs3]['data'],
        #     self.links[rs4]['data']])
        # self.draw_plot(r'$C, R$间的吞吐量', 'cr.pdf', cr)
        # self.draw_plot(r'$R, S1$间的吞吐量', 'rs1.pdf', rs1)
        # self.draw_plot(r'$R, S2$间的吞吐量', 'rs2.pdf', rs2)
        # self.draw_plot(r'$R, S3$间的吞吐量', 'rs3.pdf', rs3)
        # self.draw_plot(r'$R, S4$间的吞吐量', 'rs4.pdf', rs4)
        # self.draw_plot(r'$R$与各服务器间的吞吐量', 'rs.pdf', rs1, rs2, rs3, rs4)
        # self.draw_plot(r'总吞吐量', 'all.pdf', cr, rs1, rs2, rs3, rs4)

    def finish(self):
        # remove incomplete packet
        for l in self.links:
            data = self.links[l]
            incomple_list = []
            for pkt in data['packets']:
                packet = data['packets'][pkt]
                if 'end' not in packet:
                    incomple_list.append(pkt)
            for pkt in incomple_list:
                del data['packets'][pkt]

        for l in self.links:
            data = self.links[l]
            print l, {
                'pkt_sent': data['pkt_sent'],
                'pkt_drop': data['pkt_drop'],
                'pkt_success': len(data['packets']),
                'bytes':    data['bytes']
            }
        self.throughput()
        self.calc_flows()

def main():
    mpl.rcParams['text.usetex'] = True
    mpl.rcParams['text.latex.unicode'] = True
    mpl.rcParams['axes.unicode_minus'] = False
    FILE_NAME = 'out.tr'
    tracker = PacketTracker()
    with open(FILE_NAME, 'r') as f:
        for line in f:
            action, time, src, dst, pkt_type, pkt_size,     \
                    flags, flow_id, ip_src, ip_dst,         \
                    seq, pkt_id = line.split()
            tracker.arrive(action, float(time), src, dst, int(pkt_size),    \
                    int(flow_id), int(pkt_id))
    tracker.finish()

if __name__ == '__main__':
    main()
