source base.tcl
set server_num [setup_network]

Class Application/ClientApp -superclass Application

Application/ClientApp instproc on_start {} {
    global fileSize
    [$self agent] sendmsg [expr $fileSize + 100] "DAT_EOF"
}

Application/ClientApp instproc recv {count} {
    [finish]
}

Class Application/ServerApp -superclass Application

Application/ServerApp instproc on_start {} {
    [$self agent] listen
}

Application/ServerApp instproc send_ack {} {
    # HTTP/1.1 200 OK
    # Content-Type: application/json; charset=utf-8
    # Content-Length: 1xx
    #
    # {"result": "OK"}
    $self send 100
}
set tcp_list [$ns create-connection-list TCP/FullTcp $client TCP/FullTcp $server($target_server) 0]
set tcpc [lindex $tcp_list 0]
set tcps [lindex $tcp_list 1]
$tcpc set class_ $target_server
$tcps set class_ 0

set appc [new Application/ClientApp]
set apps [new Application/ServerApp]
$tcpc proc done_data {} {
    $self instvar server
    $server send_ack
}
$tcpc set server $apps;
$appc attach-agent $tcpc;
$apps attach-agent $tcps;
$ns at 0 "$apps start"
$ns at 0 "$appc start"
$ns run
