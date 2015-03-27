set i 0
foreach n $argv {set [incr i] $n}

set ns [new Simulator]
# set nf [open out.nam w]
set nt [open out.tr w]
set packetSize 1460
# 2GB
set fileSize  [expr 1024 * 1024 * 512]
set target_server $1
Agent/TCP set packetSize_ $packetSize
Agent/TCP/FullTcp set segsize_ $packetSize

# $ns namtrace-all $nf
$ns trace-all $nt
$ns color 1 Blue
$ns color 2 Red
$ns color 3 Yellow
$ns color 4 Green
$ns color 0 Black
proc finish {} {
    global ns nt
    # nf
    $ns flush-trace
    # close $nf
    close $nt
    exit 0
}

set client [$ns node]
set router_in [$ns node]
set router [$ns node]
set server(1) "dummy"
$ns duplex-link $client $router_in 100Mb 1ms DropTail
$ns duplex-link $router_in $router 50Mb 0ms DropTail

proc setup_network {} {
    global ns router server client target_server
    set server_num 4
    for {set i 1} {$i <= $server_num} {incr i} {
        set server($i) [$ns node]
        # $ns duplex-link-op $client $server($i) queuePos 0.5
    }
    # $ns duplex-link $router $server(1) 4Mb 15ms DropTail
    # $ns duplex-link $router $server(2) 6Mb 15ms DropTail
    # $ns duplex-link $router $server(3) 8Mb 15ms DropTail
    # $ns duplex-link $router $server(4) 10Mb 15ms DropTail
    $ns duplex-link $router $server(1) 10Mb 10ms DropTail
    $ns duplex-link $router $server(2) 10Mb 20ms DropTail
    $ns duplex-link $router $server(3) 10Mb 30ms DropTail
    $ns duplex-link $router $server(4) 10Mb 40ms DropTail
    # for {set i 1} {$i <= $server_num} {incr i} {
    #     set pair [$ns create-connection-list UDP $client Null $server($i) 0]
    #     set udp  [lindex $pair 0]
    #     set null [lindex $pair 1]
    #     set traffic($i) [new Application/Traffic/Pareto]
    #     $traffic($i) attach-agent $udp
    #     $traffic($i) set burst_time_ 5000ms
    #     $traffic($i) set idle_time_ 10000ms
    #     $traffic($i) set shape_ 1.5
    #     $udp set fid_ [expr $i + 4]
    #     $udp set packetSize_ 1000
    #     $ns at 0 "$traffic($i) start"
    # }
    # $traffic(1) set rate_ 3.2Mb
    # $traffic(2) set rate_ 4.8Mb
    # $traffic(3) set rate_ 6.4Mb
    # $traffic(4) set rate_ 8Mb
    # for {set i 1} {$i <= $server_num} {incr i} {
    #     set pair [$ns create-connection-list UDP $client Null $server($i) 0]
    #     set udp  [lindex $pair 0]
    #     set null [lindex $pair 1]
    #     set cbr($i) [new Application/Traffic/CBR]
    #     $cbr($i) attach-agent $udp
    #     $udp set packetSize_ 1000
    #     $ns at 0 "$cbr($i) start"
    # }
    # $cbr(1) set rate_ 2Mb
    # $cbr(2) set rate_ 3Mb
    # $cbr(3) set rate_ 4Mb
    # $cbr(4) set rate_ 5Mb
    # $ns at 0 "$cbr($target_server) start"
    # for {set i 1} {$i <= $server_num} {incr i} {
    #     set tcp [$ns create-connection TCP $client TCPSink $server($i) 0]
    #     set ftp [new Application/FTP]
    #     $ftp attach-agent $tcp
    #     $ns at 0 "$ftp start"
    # }
    # set tcp [$ns create-connection TCP $client TCPSink $server($target_server) 0]
    # set ftp [new Application/FTP]
    # $ftp attach-agent $tcp
    # $ns at 0 "$ftp start"
    return $server_num
}
