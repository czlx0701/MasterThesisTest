set ns [new Simulator]
set nf [open out.nam w]
set nt [open out.tr w]
set packetSize 1460
# 2GB
set fileSize  [expr 1024 * 1024 * 20]
set target_server 1
Agent/TCP set packetSize_ $packetSize
Agent/TCP/FullTcp set segsize_ $packetSize

$ns namtrace-all $nf
$ns trace-all $nt
$ns color 1 Blue
$ns color 2 Red
$ns color 3 Yellow
$ns color 4 Green
$ns color 0 Black
proc finish {} {
    global ns nf nt
    $ns flush-trace
    close $nf
    close $nt
    exit 0
}

set client [$ns node]
set router [$ns node]
set server(1) "dummy"
$ns duplex-link $client $router 10Mb 1ms DropTail

proc setup_network {} {
    global ns router server
    set server_num 4
    for {set i 1} {$i <= $server_num} {incr i} {
        set server($i) [$ns node]
        $ns duplex-link $router $server($i) 1Mb 10ms DropTail
        # $ns duplex-link-op $client $server($i) queuePos 0.5
    }
    return $server_num
}
